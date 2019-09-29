from typing import List, Optional, NewType, Any

import datetime

from eth_keys import keys
from eth_utils import to_checksum_address

from celery import chain, signature

import requests

import config
from eth_manager.exceptions import WrongContractNameError, PreBlockchainError
from eth_manager import utils

Id = NewType("Id", int)
IdList = List[Id]

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

    def process_send_eth_transaction(self, transaction_id,
                                     recipient_address, amount):

        partial_txn_dict = {
            'to': recipient_address,
            'value': amount
        }

        return self.process_transaction(transaction_id, partial_txn_dict=partial_txn_dict)


    def process_function_transaction(self, transaction_id,
                                     contract_name, function_name, args=None, kwargs=None, gas_limit=None):

        args = args or tuple()
        if not isinstance(args, (list, tuple)):
            args = [args]

        kwargs = kwargs or dict()

        function = self.registry.get_contract_function(contract_name, function_name)\

        bound_function = function(*args, **kwargs)

        return self.process_transaction(transaction_id, bound_function, gas_limit=gas_limit)

    def process_transaction(self,
                            transaction_id,
                            function=None,
                            partial_txn_dict=None,
                            gas_limit=None,
                            gas_price=None):

        signing_wallet_obj = self.persistence_interface.get_transaction_signing_wallet(transaction_id)

        nonce, transaction_id = self.persistence_interface\
            .claim_transaction_nonce(signing_wallet_obj, transaction_id)


        txn = {
            'chainId': self.ethereum_chain_id,
            'gas': gas_limit or self.gas_limit,
            'gasPrice': gas_price or self.get_gas_price(),
            'nonce': nonce
        }

        if function:
            txn = function.buildTransaction(txn)
        else:
            txn = {**txn, **partial_txn_dict}

        signed_txn = self.w3.eth.account.signTransaction(txn, private_key=signing_wallet_obj.private_key)


        try:
            result = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)

        except ValueError as e:

            raise PreBlockchainError(f'Transaction {transaction_id}: {str(e)}')

        # If we've made it this far, the nonce will(?) be consumed
        transaction_data = {
            'hash': signed_txn.hash.hex(),
            'nonce': nonce,
            'submitted_date': str(datetime.datetime.utcnow()),
            'nonce_consumed': True
        }

        print('***************Data for transaction {}:***************'.format(transaction_id))
        print(transaction_data)

        self.persistence_interface.update_transaction_data(transaction_id, transaction_data)

        return transaction_id

    def check_transaction_response(self, transaction_id):

        transaction_hash = self.persistence_interface.get_transaction_hash_from_id(transaction_id)

        result = self.check_transaction_hash(transaction_hash)

        self.persistence_interface.update_transaction_data(transaction_id, result)

        if result.get('status') == 'SUCCESS':
            unstarted_dependents = self.persistence_interface.get_unstarted_dependents(transaction_id)

            for task in unstarted_dependents:
                print('Starting dependent task: {}'.format(task.id))
                signature(utils.eth_endpoint('_attempt_transaction'), args=(task.id, )).delay()

        return result.get('status')

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

    def attempt_transaction(self, task_id):

        unsatisfied_dependee_tasks = self.persistence_interface.unstatisfied_task_dependencies(task_id)
        if len(unsatisfied_dependee_tasks) > 0:
            print('Skipping: dependee tasks {} unsatisfied'.format([task.id for task in unsatisfied_dependee_tasks]))
            return

        transaction_obj = self.persistence_interface.create_blockchain_transaction(task_id)

        task_object = self.persistence_interface.get_task_from_id(task_id)

        if task_object.is_send_eth:
            print(f'Starting Send Eth Transaction for {task_id}.')
            chain1 = signature(utils.eth_endpoint('_process_send_eth_transaction'),
                          args=(transaction_obj.id,
                                task_object.recipient_address,
                                task_object.amount))
        else:
            print(f'Starting {task_object.function} Transaction for {task_id}.')
            chain1 = signature(utils.eth_endpoint('_process_function_transaction'),
                               args=(transaction_obj.id,
                                     task_object.contract,
                                     task_object.function,
                                     task_object.args,
                                     task_object.kwargs,
                                     task_object.gas_limit))

        chain2 = signature(utils.eth_endpoint('_check_transaction_response'))

        error_callback = signature(utils.eth_endpoint('_log_error'), args=(transaction_obj.id,))

        return chain([chain1, chain2]).on_error(error_callback).delay()

    def get_signing_wallet_object(self, signing_address, encrypted_private_key):
        if signing_address:

            signing_wallet_obj = self.persistence_interface.get_wallet_by_address(signing_address)

            if signing_wallet_obj is None:
                raise Exception('Private key for address {} not found'.format(signing_address))

        elif encrypted_private_key:

            signing_wallet_obj = self.persistence_interface.get_wallet_by_encrypted_private_key(encrypted_private_key)

            if not signing_wallet_obj:
                signing_wallet_obj = self.persistence_interface.create_blockchain_wallet_from_encrypted_private_key(
                    encrypted_private_key=encrypted_private_key)
        else:
            raise Exception("Must provide encrypted private key")

        return signing_wallet_obj

    def log_error(self, request, exc, traceback, transaction_id):
        data = {
            'error': type(exc).__name__,
            'message': str(exc.args[0]),
            'status': 'FAILED'
        }

        self.persistence_interface.update_transaction_data(transaction_id, data)

    def get_serialised_task_from_id(self, id):

        return self.persistence_interface.get_serialised_task_from_id(id)

    def call_contract_function(self, contract_name: str, function_name: str,
                               args: Optional[tuple] = None, kwargs: Optional[dict] = None) -> Any:
        """
        The main call entrypoint for the transaction. This task completes quickly,
        so can be called synchronously.

        :param encrypted_private_key: private key of the wallet making the transaction, encrypted usign key from settings
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
                                        contract_name_or_address: str, function_name: str,
                                        args: Optional[tuple] = None, kwargs: Optional[dict] = None,
                                        signing_address: Optional[str] = None, encrypted_private_key: Optional[str]=None,
                                        gas_limit: Optional[int] = None,
                                        dependent_on_tasks: Optional[IdList] = None) -> int:
        """
        The main transaction entrypoint for the processor. This task completes quickly,
        so can be called synchronously in order to retrieve a task ID

        :param contract_name_or_address: name or address of the contract for the function
        :param function_name: name of the function
        :param args: arguments for the function
        :param kwargs: keyword arguments for the function
        :param signing_address: address of the wallet signing the txn
        :param encrypted_private_key: private key of the wallet making the transaction, encrypted usign key from settings
        :param gas_limit: limit on the amount of gas txn can use. Overrides system default
        :param dependent_on_tasks: a list of task ids that must succeed before this task will be attempted
        :return: task_id
        """

        signing_wallet_obj = self.get_signing_wallet_object(signing_address, encrypted_private_key)

        task = self.persistence_interface.create_function_task(signing_wallet_obj,
                                                               contract_name_or_address, function_name, args, kwargs,
                                                               gas_limit, dependent_on_tasks)

        # Attempt Create Async Transaction
        signature(utils.eth_endpoint('_attempt_transaction'), args=(task.id,)).delay()

        # Immediately return task ID
        return task.id

    def send_eth(self,
                 amount_wei: int,
                 recipient_address: str,
                 signing_address: Optional[str] = None, encrypted_private_key: Optional[str] = None,
                 dependent_on_tasks: Optional[IdList] = None) -> int:
        """
        The main entrypoint sending eth. This task completes quickly,
        so can be called synchronously in order to retrieve a task ID

        :param amount_wei: the amount in WEI to send
        :param recipient_address: the recipient address
        :param signing_address: address of the wallet signing the txn
        :param encrypted_private_key: private key of the wallet making the transaction, encrypted usign key from settings
        :param dependent_on_tasks: a list of task ids that must succeed before this task will be attempted
        :return: task_id
        """

        signing_wallet_obj = self.get_signing_wallet_object(signing_address, encrypted_private_key)

        task = self.persistence_interface.create_send_eth_task(signing_wallet_obj,
                                                               recipient_address, amount_wei,
                                                               dependent_on_tasks)

        # Attempt Create Async Transaction
        signature(utils.eth_endpoint('_attempt_transaction'), args=(task.id,)).delay()

        # Immediately return task ID
        return task.id

    def __init__(self,
                 ethereum_chain_id,
                 w3,
                 gas_price_gwei,
                 gas_limit,
                 persistence_interface):

            self.registry = ContractRegistry(w3)

            self.ethereum_chain_id = int(ethereum_chain_id)
            self.w3 = w3

            self.gas_price = self.w3.toWei(gas_price_gwei, 'gwei')
            self.gas_limit = gas_limit
            self.transaction_max_value = self.gas_price * self.gas_limit

            self.persistence_interface = persistence_interface


