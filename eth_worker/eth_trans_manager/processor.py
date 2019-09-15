from typing import List, Optional, NewType, Any

import json, base64, ssl, datetime, random, time

from sqlalchemy import (
    or_,
    and_
)

from eth_keys import keys
from eth_utils import to_checksum_address

from celery import chain, Celery, signature

import requests

import config
from eth_trans_manager.exceptions import WrongContractNameError, PreBlockchainError
from eth_trans_manager.models import BlockchainTransaction, BlockchainTask, BlockchainAddress, session

Id = NewType("Id", int)
IdList = List[Id]

class SQLAlchemyDataStore(object):

    def _fail_expired_transactions(self):
        expire_time = datetime.datetime.utcnow() - datetime.timedelta(
            seconds=self.PENDING_TRANSACTION_EXPIRY_SECONDS
        )

        (session.query(BlockchainTransaction)
         .filter(and_(BlockchainTransaction.status == 'PENDING',
                      BlockchainTransaction.created < expire_time))
         .update({BlockchainTransaction.status: 'FAILED',
                  BlockchainTransaction.error: 'Timeout Error'},
                 synchronize_session=False))

    def _calculate_nonce(self, singing_address_obj, transaction_id, starting_nonce=0):

        self._fail_expired_transactions()

        # First find the highest *continuous* nonce that isn't either pending, or consumed
        # (failed or succeeded on blockchain)

        likely_consumed_nonces = (
            session.query(BlockchainTransaction)
                .filter(BlockchainTransaction.signing_address == singing_address_obj)
                .filter(
                    and_(
                        or_(BlockchainTransaction.nonce_consumed == True,
                            BlockchainTransaction.status == 'PENDING'),
                        BlockchainTransaction.nonce >= starting_nonce
                    )
                )
                .all())

        # Use a set to find continous nonces because txns in db may be out of order
        nonce_set = set()
        nonce_to_id = {}
        for txn in likely_consumed_nonces:
            nonce_set.add(txn.nonce)
            if txn.nonce > nonce_to_id.get(txn.nonce, 0):
                nonce_to_id[txn.nonce] = txn.id

        next_nonce = starting_nonce
        highest_valid_id = None
        while next_nonce in nonce_set:
            highest_valid_id = nonce_to_id.get(next_nonce, highest_valid_id)
            next_nonce += 1

        # if highest_valid_id is None, find it from db
        if highest_valid_id is None:
            highest_valid_txn = (
                session.query(BlockchainTransaction)
                    .filter(BlockchainTransaction.signing_address == singing_address_obj)
                    .filter(
                        and_(
                            or_(BlockchainTransaction.nonce_consumed == True,
                                BlockchainTransaction.status == 'PENDING'),
                            BlockchainTransaction.nonce <= starting_nonce
                        )
                    )
                    .order_by(BlockchainTransaction.id.desc())
                    .first())
            highest_valid_id = getattr(highest_valid_txn,'id',0)

        # Now find all transactions that are from the same address
        # and have a txn ID bound by the top consumed nonce and the current txn.
        # These txns are in a similar state to the current will be allocated nonces very shortly
        # Because they have lower IDs, they get precendent over the nonces

        live_txns_from_same_address = (
            session.query(BlockchainTransaction)
                .filter(BlockchainTransaction.signing_address == singing_address_obj)
                .filter(BlockchainTransaction.status == 'PENDING')
                .filter(and_(BlockchainTransaction.id > highest_valid_id,
                             BlockchainTransaction.id < transaction_id))
                .all())

        return next_nonce + len(live_txns_from_same_address)

    def claim_transaction_nonce(self, signing_address_obj, transaction_id):

        network_nonce = self.w3.eth.getTransactionCount(signing_address_obj.address, block_identifier='pending')

        blockchain_transaction = session.query(BlockchainTransaction).get(transaction_id)

        calculated_nonce = self._calculate_nonce(signing_address_obj, transaction_id, network_nonce)

        blockchain_transaction.signing_address = signing_address_obj
        blockchain_transaction.nonce = calculated_nonce
        blockchain_transaction.status = 'PENDING'

        session.commit()

        gauranteed_clash_free = False

        clash_fix_attempts = 0
        while not gauranteed_clash_free and clash_fix_attempts < 200:
            clash_fix_attempts += 1
            # Occasionally two workers will hit the db at the same time and claim the same nonce

            nonce_clash_txns = (session.query(BlockchainTransaction)
                              .filter(BlockchainTransaction.id != transaction_id)
                              .filter(BlockchainTransaction.signing_address == signing_address_obj)
                              .filter(BlockchainTransaction.status == 'PENDING')
                              .filter(BlockchainTransaction.nonce == blockchain_transaction.nonce)
                              .all())


            if len(nonce_clash_txns) > 0:
                # If there is a clash, just try again
                print('\n ~~~~~~~~Cash Fix {} for txn {} with nonce {}~~~~~~~~'
                    .format(clash_fix_attempts, transaction_id, blockchain_transaction.nonce))
                print(nonce_clash_txns)

                lower_txn_ids = 0
                for txn in nonce_clash_txns:
                    if txn.id < transaction_id:
                        lower_txn_ids += 1

                if lower_txn_ids != 0:
                    print('Incrementing nonce by {}'.format(lower_txn_ids))
                    blockchain_transaction.nonce = blockchain_transaction.nonce + lower_txn_ids
                    session.commit()
                else:
                    print('Transaction has lowest ID, taking nonce')
                    gauranteed_clash_free = True

            else:
                gauranteed_clash_free = True

        print('@@@@@@@@@@@@@@ tx {} using nonce {} @@@@@@@@@@@@@@'.format(transaction_id, calculated_nonce))

        session.commit()

        return calculated_nonce, blockchain_transaction.id

    def update_transaction_data(self, transaction_id, transaction_data):

        transaction = session.query(BlockchainTransaction).get(transaction_id)

        for attribute in transaction_data:
            setattr(transaction, attribute, transaction_data[attribute])

        session.commit()

    def create_blockchain_transaction(self, task_id):

        task = session.query(BlockchainTask).get(task_id)

        blockchain_transaction = BlockchainTransaction(signing_address=task.signing_address)

        session.add(blockchain_transaction)

        if task:
            blockchain_transaction.task = task

        session.commit()

        return blockchain_transaction

    def get_transaction_hash_from_id(self, transaction_id):
        transaction = session.query(BlockchainTransaction).get(transaction_id)

        return transaction.hash

    def get_transaction_signing_address(self, transaction_id):

        transaction = session.query(BlockchainTransaction).get(transaction_id)

        return transaction.signing_address

    def get_unstarted_dependents(self, transaction_id):
        transaction = session.query(BlockchainTransaction).get(transaction_id)

        unstarted_dependents = []
        for dependent_task in transaction.task.dependents:
            if dependent_task.status == 'UNSTARTED':
                unstarted_dependents.append(dependent_task)

        return unstarted_dependents

    def unstatisfied_task_dependencies(self, task_id):
        task = session.query(BlockchainTask).get(task_id)

        unsatisfied = []
        for dependee in task.dependees:
            if dependee.status != 'SUCCESS':
                unsatisfied.append(dependee)

        return unsatisfied

    def create_transaction_task(self, address_obj, contract,
                                function, args=None, kwargs=None,
                                dependent_on_tasks=None):

        if dependent_on_tasks is None:
            dependent_on_tasks = []

        task = BlockchainTask(signing_address=address_obj,
                              contract=contract,
                              function=function,
                              args=args,
                              kwargs=kwargs)

        session.add(task)

        for task_id in dependent_on_tasks:
            dependee_task = session.query(BlockchainTask).get(task_id)
            task.dependees.append(dependee_task)

        session.commit()

        return task

    def create_account(self, encrypted_private_key=None):

        if session.query(BlockchainAddress).filter_by(encrypted_private_key=encrypted_private_key).first():
            raise Exception("Account for provided private key already exists")

        account = BlockchainAddress(encrypted_private_key=encrypted_private_key)

        session.add(account)

        session.commit()

        return account

    def get_account_by_address(self, address):
        return session.query(BlockchainAddress).filter(BlockchainAddress.address == address).first()

    def get_account_by_encrypted_private_key(self, encrypted_private_key):
         return session.query(BlockchainAddress).filter(
             BlockchainAddress.encrypted_private_key == encrypted_private_key).first()

    def __init__(self, w3, PENDING_TRANSACTION_EXPIRY_SECONDS=300):

        self.w3 = w3

        self.PENDING_TRANSACTION_EXPIRY_SECONDS = PENDING_TRANSACTION_EXPIRY_SECONDS

class ContractRegistry(object):

    def _get_contract_name(self, contract):
        bytes_contract_name = contract.functions.name().call()
        null_byte_stripped_name = bytes(filter(None,bytes_contract_name))
        return null_byte_stripped_name.decode()

    def _check_contract_name(self, contract_name, expected_name):

        print('Expecting Contract: ' + expected_name)
        print('Found Contract: ' + contract_name)
        if contract_name != expected_name:
            raise WrongContractNameError

    def register_contract(self, contract_address, abi, contract_name=None, require_name_matches=False):
        checksum_address = to_checksum_address(contract_address)

        contract = self.w3.eth.contract(address=checksum_address, abi=abi)

        found_contract_name = self._get_contract_name(contract)

        if require_name_matches:
            self._check_contract_name(found_contract_name, contract_name)

        if contract_name in self.contracts_by_name:
            raise Exception("Contract with name {} already registered".format(contract_name))

        if contract_name:
            self.contracts_by_name[contract_name] = contract

        self.contracts_by_address[contract_address] = contract

    def get_contract(self, contract_name_or_address):
        contract = self.contracts_by_address.get(contract_name_or_address)\
                   or self.contracts_by_name.get(contract_name_or_address)

        if not contract:
            raise Exception('Contract not found for name or address: {}'.format(contract_name_or_address))

        return contract

    def get_contract_function(self, contract_name_or_address, function_name):
        contract = self.get_contract(contract_name_or_address)
        return getattr(contract.functions, function_name)

    def __init__(self, w3):

        self.w3 = w3
        self.contracts_by_address = {}
        self.contracts_by_name = {}


class TransactionProcessor(object):

    def private_key_to_address(self, private_key):

        if isinstance(private_key, str):
            private_key = bytearray.fromhex(private_key.replace('0x',''))

        return keys.PrivateKey(private_key).public_key.to_checksum_address()

    def get_gas_price(self, target_transaction_time=None):

        if not target_transaction_time:
            target_transaction_time = config.ETH_TARGET_TRANSACTION_TIME

        try:
            gas_price_req = requests.get(config.ETH_GAS_PRICE_PROVIDER + '/price',
                                         params={'max_wait_seconds': target_transaction_time}).json()

            gas_price = min(gas_price_req['gas_price'], self.gas_price)

            print('gas price: {}'.format(gas_price))

        except Exception as e:
            gas_price = self.gas_price

        return gas_price

    def process_function_transaction(self, transaction_id,
                                     contract_name, function_name, args=None, kwargs=None):

        args = args or tuple()
        if not isinstance(args, (list, tuple)):
            args = [args]

        kwargs = kwargs or dict()

        function = self.registry.get_contract_function(contract_name, function_name)\

        bound_function = function(*args, **kwargs)

        return self.process_transaction(transaction_id, bound_function)

    def process_transaction(self,
                            transaction_id,
                            function=None,
                            partial_txn_dict=None,
                            gas_limit_override=None,
                            gas_price_override=None):

        singing_address_obj = self.persistence_model.get_transaction_signing_address(transaction_id)

        nonce, transaction_id = self.persistence_model\
            .claim_transaction_nonce(singing_address_obj, transaction_id)


        txn = {
            'chainId': self.ethereum_chain_id,
            'gas': gas_limit_override or self.gas_limit,
            'gasPrice': gas_price_override or self.get_gas_price(),
            'nonce': nonce
        }

        if function:
            txn = function.buildTransaction(txn)
        else:
            txn = {**txn, **partial_txn_dict}

        signed_txn = self.w3.eth.account.signTransaction(txn, private_key=singing_address_obj.private_key)


        try:
            result = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)

        except ValueError as e:

            raise PreBlockchainError(str(e))

        # If we've made it this far, the nonce will(?) be consumed
        transaction_data = {
            'hash': signed_txn.hash.hex(),
            'nonce': nonce,
            'submitted_date': str(datetime.datetime.utcnow()),
            'nonce_consumed': True
        }

        print('***************Data for transaction {}:***************'.format(transaction_id))
        print(transaction_data)

        self.persistence_model.update_transaction_data(transaction_id, transaction_data)

        return transaction_id

    def check_transaction_response(self, transaction_id):

        transaction_hash = self.persistence_model.get_transaction_hash_from_id(transaction_id)

        result = self.check_transaction_hash(transaction_hash)

        self.persistence_model.update_transaction_data(transaction_id, result)

        if result.get('status') == 'SUCCESS':
            unstarted_dependents = self.persistence_model.get_unstarted_dependents(transaction_id)

            for task in unstarted_dependents:
                print('Starting dependent task: {}'.format(task.id))
                signature('eth_trans_manager.celery_tasks._attempt_transaction',
                          args=(task.id, task.contract, task.function, task.args, task.kwargs)).delay()

            return True

        return False

    def check_transaction_hash(self, tx_hash):

        print('watching txn: {} at {}'.format(tx_hash, datetime.datetime.utcnow()))

        tx_receipt = self.w3.eth.getTransactionReceipt(tx_hash)

        def print_and_return(return_dict):
            print('{} for txn: {}'.format(return_dict.get('status'),tx_hash))
            return return_dict

        if tx_receipt is None:
            return print_and_return({'status': 'PENDING'})

        mined_date = str(datetime.datetime.utcnow())

        if tx_receipt.blockNumber is None:
            return print_and_return({'status': 'PENDING', 'message': 'Next Block'})

        if tx_receipt.status == 1:

            return print_and_return({'status': 'SUCCESS',
                                      'block': tx_receipt.blockNumber,
                                      'mined_date': mined_date})

        else:
           return print_and_return({'status': 'FAILED',
                                    'error': 'Blockchain Error',
                                    'block': tx_receipt.blockNumber,
                                    'mined_date': mined_date})

    def attempt_transaction(self, task_id, contract_name, function_name, args=None, kwargs=None):

        unsatisfied_dependee_tasks = self.persistence_model.unstatisfied_task_dependencies(task_id)
        if len(unsatisfied_dependee_tasks) > 0:
            print('Skipping: dependee tasks {} unsatisfied'.format([task.id for task in unsatisfied_dependee_tasks]))
            return

        transaction_obj = self.persistence_model.create_blockchain_transaction(task_id)

        chain1 = signature('eth_trans_manager.celery_tasks._process_function_transaction',
                          args=(transaction_obj.id, contract_name, function_name, args, kwargs))

        chain2 = signature('eth_trans_manager.celery_tasks._check_transaction_response')

        error_callback = signature('eth_trans_manager.celery_tasks._log_error', args=(transaction_obj.id,))

        return chain([chain1, chain2]).on_error(error_callback).delay()

    def log_error(self, request, exc, traceback, transaction_id):
        data = {
            'error': type(exc).__name__,
            'message': str(exc.args[0]),
            'status': 'FAILED'
        }

        self.persistence_model.update_transaction_data(transaction_id, data)

    def call_contract_function(self, contract_name: str, function_name: str,
                               args: Optional[tuple] = None, kwargs: Optional[dict] = None) -> Any:
        """
        The main call entrypoint for the transaction. This task completes quickly,
        so can be called synchronously.

        :param encrypted_private_key: private key of the account making the transaction, encrypted using key from settings
        :param contract_name: name of the contract for the function
        :param function_name: name of the function
        :param args: arguments for the function
        :param kwargs: keyword arguments for the function
        :param dependent_on_tasks: a list of task ids that must succeed before this task will be attempted
        :return: the result of the contract call
        """

        args = args or tuple()
        if not isinstance(args, (list, tuple)):
            args = [args]

        kwargs = kwargs or dict()

        function = self.registry.get_contract_function(contract_name, function_name)(*args, **kwargs)

        return function.call()


    def transact_with_contract_function(self,
                                        encrypted_private_key: str,
                                        contract_name_or_address: str, function_name: str,
                                        args: Optional[tuple] = None, kwargs: Optional[dict] = None,
                                        # address: Optional[str]=None, encrypted_private_key: Optional[str]=None,
                                        dependent_on_tasks: Optional[IdList] = None) -> int:
        """
        The main transaction entrypoint for the processor. This task completes quickly,
        so can be called synchronously in order to retrieve a task ID

        :param contract_name_or_address: name or address of the contract for the function
        :param function_name: name of the function
        :param args: arguments for the function
        :param kwargs: keyword arguments for the function
        :param address: address of the account signing the txn
        :param encrypted_private_key: private key of the account making the transaction, encrypted using key from settings
        :param dependent_on_tasks: a list of task ids that must succeed before this task will be attempted
        :return: task_id
        """

        # if address:
        #
        #     address_obj = self.persistence_model.get_account_by_address(address)
        #
        #     if address_obj is None:
        #         raise Exception('Private key for address {} not found'.format(address))

        if encrypted_private_key:

            address_obj = self.persistence_model.get_account_by_encrypted_private_key(encrypted_private_key)

            if not address_obj:
                address_obj = self.persistence_model.create_account(encrypted_private_key=encrypted_private_key)
        else:
            raise Exception("Must provide encrypted private key")

        task = self.persistence_model.create_transaction_task(address_obj,
                                                              contract_name_or_address, function_name, args, kwargs,
                                                              dependent_on_tasks)

        # Create Async Task
        signature('eth_trans_manager.celery_tasks._attempt_transaction',
                  args=(task.id, contract_name_or_address, function_name, args, kwargs)).delay()

        # Immediately return task ID
        return task.id

    def __init__(self,
                 ethereum_chain_id,
                 w3,
                 gas_price_gwei,
                 gas_limit,
                 persistence_model=SQLAlchemyDataStore):

            self.registry = ContractRegistry(w3)

            self.ethereum_chain_id = int(ethereum_chain_id)
            self.w3 = w3

            self.gas_price = self.w3.toWei(gas_price_gwei, 'gwei')
            self.gas_limit = gas_limit
            self.transaction_max_value = self.gas_price * self.gas_limit

            self.persistence_model = persistence_model(self.w3)
