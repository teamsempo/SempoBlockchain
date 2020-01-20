from typing import Optional, Any

import datetime

from eth_keys import keys

from celery import chain, signature

import requests

import config
from eth_manager.exceptions import PreBlockchainError, TaskRetriesExceededError
from eth_manager import utils
from eth_manager.contract_registry import ContractRegistry
from sempo_types import UUIDList, UUID

RETRY_TRANSACTION_BASE_TIME = 2
ETH_CHECK_TRANSACTION_BASE_TIME = 2
ETH_CHECK_TRANSACTION_RETRIES_TIME_LIMIT = 4

class TransactionProcessor(object):

    def private_key_to_address(self, private_key):

        if isinstance(private_key, str):
            private_key = bytearray.fromhex(private_key.replace('0x', ''))

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

    def topup_if_required(self, wallet, posterior_task_uuid):
        balance = self.w3.eth.getBalance(wallet.address)

        wei_topup_threshold = wallet.wei_topup_threshold
        wei_target_balance = wallet.wei_target_balance or 0

        if balance <= wei_topup_threshold and wei_target_balance > balance:
            sig = signature(utils.eth_endpoint('send_eth'),
                            kwargs={
                                'signing_address': config.MASTER_WALLET_ADDRESS,
                                'amount_wei': wei_target_balance - balance,
                                'recipient_address': wallet.address,
                                'prior_tasks': [],
                                'posterior_tasks': [posterior_task_uuid]
                            })

            task_uuid = utils.execute_task(sig)

            self.persistence_interface.set_wallet_last_topup_task_uuid(wallet.address, task_uuid)

            return task_uuid

        return None

    def process_send_eth_transaction(self, transaction_id,
                                     recipient_address, amount, task_id=None):

        partial_txn_dict = {
            'to': recipient_address,
            'value': amount
        }

        print(f'\n##Tx {transaction_id}, task {task_id}: Sending Eth \n'
              f'to: {recipient_address} \n'
              f'amount: {amount}')

        return self.process_transaction(transaction_id, partial_txn_dict=partial_txn_dict, gas_limit=100000)

    def typecast_argument(self, argument):
        if isinstance(argument, dict) and argument.get('type') == 'bytes':
                return argument.get('data').encode()
        return argument

    def process_function_transaction(self, transaction_id, contract_address, abi_type,
                                     function_name, args=None, kwargs=None, gas_limit=None, task_id=None):

        args = args or tuple()
        if not isinstance(args, (list, tuple)):
            args = [args]
        args = [self.typecast_argument(a) for a in args]

        kwargs = kwargs or dict()
        kwargs = {k: self.typecast_argument(v) for k, v in kwargs.items()}

        print(f'\n##Tx {transaction_id}, task {task_id}: Transacting with Function {function_name} \n'
              f'Args: {args} \n'
              f'Kwargs: {kwargs}')

        function = self.registry.get_contract_function(contract_address, function_name, abi_type)

        bound_function = function(*args, **kwargs)

        return self.process_transaction(transaction_id, bound_function, gas_limit=gas_limit)

    def process_deploy_contract_transaction(self, transaction_id, contract_name,
                                            args=None, kwargs=None, gas_limit=None, task_id=None):

        args = args or tuple()
        if not isinstance(args, (list, tuple)):
            args = [args]

        kwargs = kwargs or dict()

        print(f'\n##Tx {transaction_id}, task {task_id}: Deploying Contract {contract_name} \n'
              f'Args: {args} \n'
              f'Kwargs: {kwargs}')

        contract = self.registry.get_compiled_contract(contract_name)

        constructor = contract.constructor(*args, **kwargs)

        return self.process_transaction(transaction_id, constructor, gas_limit=gas_limit)

    def process_transaction(self,
                            transaction_id,
                            unbuilt_transaction=None,
                            partial_txn_dict=None,
                            gas_limit=None,
                            gas_price=None):

        try:

            chainId = self.ethereum_chain_id
            gasPrice = gas_price or self.gas_price
            # gasPrice = gas_price or self.get_gas_price()

            signing_wallet_obj = self.persistence_interface.get_transaction_signing_wallet(transaction_id)

            if gas_limit:
                gas = gas_limit
            else:
                try:
                    gas = unbuilt_transaction.estimateGas({
                        'from': signing_wallet_obj.address,
                        'gasPrice': gasPrice
                    })
                except ValueError as e:
                    print("Estimate Gas Failed. Remedy by specifying gas limit.")

                    raise e

            nonce, transaction_id = self.persistence_interface.locked_claim_transaction_nonce(
                signing_wallet_obj, transaction_id
            )

            metadata = {
                'gas': gas_limit or min(int(gas*1.2), 8000000),
                'gasPrice': gasPrice,
                'nonce': nonce
            }

            if chainId:
                metadata['chainId'] = chainId

            if unbuilt_transaction:
                txn = unbuilt_transaction.buildTransaction(metadata)
            else:
                txn = {**metadata, **partial_txn_dict}

            signed_txn = self.w3.eth.account.signTransaction(txn, private_key=signing_wallet_obj.private_key)

            try:
                print('@@@@@@@@@@@@@@ tx {} using nonce {} @@@@@@@@@@@@@@'.format(transaction_id, nonce))

                result = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)

            except ValueError as e:

                message = f'Transaction {transaction_id}: {str(e)}'
                exc = PreBlockchainError(message, False)
                self.log_error(None, exc, None, transaction_id)

                raise PreBlockchainError(message, True)

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

        except Exception as e:

            # Attempt a new transaction if there's any error, but still raise
            transaction_object = self.persistence_interface.get_transaction(transaction_id)
            try:
                self.new_transaction_attempt(transaction_object.task)
            except TaskRetriesExceededError:
                pass

            raise e

    def get_unstarted_posteriors(self, task):

        unstarted_posteriors = []
        for posterior in task.posterior_tasks:
            if posterior.status == 'UNSTARTED':
                unstarted_posteriors.append(posterior)

        return unstarted_posteriors

    def check_transaction_response(self, celery_task, transaction_id):
        def transaction_response_countdown():
            t = lambda retries: ETH_CHECK_TRANSACTION_BASE_TIME * 2 ** retries

            # If the system has been longer than the max retry period
            # if previous_result:
            #     submitted_at = datetime.strptime(previous_result['submitted_date'], "%Y-%m-%d %H:%M:%S.%f")
            #     if (datetime.utcnow() - submitted_at).total_seconds() > ETH_CHECK_TRANSACTION_RETRIES_TIME_LIMIT:
            #         if self.request.retries != self.max_retries:
            #             self.request.retries = self.max_retries - 1
            #
            #         return 0

            return t(celery_task.request.retries)

        try:
            transaction_object = self.persistence_interface.get_transaction(transaction_id)

            task = transaction_object.task

            transaction_hash = transaction_object.hash

            result = self.check_transaction_hash(transaction_hash)

            self.persistence_interface.update_transaction_data(transaction_id, result)

            status = result.get('status')

            print(f'Status for transaction {transaction_object.id} of task UUID {task.uuid} is:'
            f'\n {status}')

            if status == 'SUCCESS':

                unstarted_posteriors = self.get_unstarted_posteriors(task)

                for dep_task in unstarted_posteriors:
                    print('Starting posterior task: {}'.format(dep_task.uuid))
                    signature(utils.eth_endpoint('_attempt_transaction'), args=(dep_task.uuid,)).delay()

                self.persistence_interface.set_task_status_text(task, 'SUCCESS')

            if status == 'PENDING':
                celery_task.request.retries = 0
                raise Exception("Need Retry")

            if status == 'FAILED':
                self.new_transaction_attempt(task)

        except TaskRetriesExceededError as e:
            pass

        except Exception as e:
            print(e)
            celery_task.retry(countdown=transaction_response_countdown())

    def check_transaction_hash(self, tx_hash):

        print('watching txn: {} at {}'.format(tx_hash, datetime.datetime.utcnow()))

        tx_receipt = self.w3.eth.getTransactionReceipt(tx_hash)

        def print_and_return(return_dict):
            # Not printing here currently because the method above does it
            # print('{} for txn: {}'.format(return_dict.get('status'), tx_hash))
            return return_dict

        if tx_receipt is None:
            return print_and_return({'status': 'PENDING'})

        mined_date = str(datetime.datetime.utcnow())

        if tx_receipt.blockNumber is None:
            return print_and_return({'status': 'PENDING', 'message': 'Next Block'})

        if tx_receipt.status == 1:

            return print_and_return({
                'status': 'SUCCESS',
                'block': tx_receipt.blockNumber,
                'contract_address': tx_receipt.contractAddress,
                'mined_date': mined_date
            })

        else:
           return print_and_return({
               'status': 'FAILED',
               'error': 'Blockchain Error',
               'block': tx_receipt.blockNumber,
               'mined_date': mined_date
           })

    def get_unsatisfied_prior_tasks(self, task):

        unsatisfied = []
        for prior in task.prior_tasks:
            if prior.status != 'SUCCESS':
                unsatisfied.append(prior)

        return unsatisfied


    def attempt_transaction(self, task_uuid):

        task = self.persistence_interface.get_task_from_uuid(task_uuid)

        unsatisfied_prior_tasks = self.get_unsatisfied_prior_tasks(task)

        if len(unsatisfied_prior_tasks) > 0:
            print('Skipping {}: prior tasks {} unsatisfied'.format(
                task.id,
                [f'{u.id} ({u.uuid})' for u in unsatisfied_prior_tasks]))
            return

        topup_uuid = self.topup_if_required(task.signing_wallet, task_uuid)

        if topup_uuid:
            print(f'Skipping {task.id}: Topup required')
            return


        transaction_obj = self.persistence_interface.create_blockchain_transaction(task_uuid)

        task_object = self.persistence_interface.get_task_from_uuid(task_uuid)

        number_of_attempts = len(task_object.transactions)

        attempt_info = f'\nAttempt number: {number_of_attempts} ' \
                       f' for invocation round: {task_object.previous_invocations + 1}'

        if task_object.type == 'SEND_ETH':

            transfer_amount = int(task_object.amount)

            print(f'Starting Send Eth Transaction for {task_uuid}.' + attempt_info)
            chain1 = signature(utils.eth_endpoint('_process_send_eth_transaction'),
                          args=(transaction_obj.id,
                                task_object.recipient_address,
                                transfer_amount,
                                task_object.id))

        elif task_object.type == 'FUNCTION':
            print(f'Starting {task_object.function} Transaction for {task_uuid}.' + attempt_info)
            chain1 = signature(utils.eth_endpoint('_process_function_transaction'),
                               args=(transaction_obj.id,
                                     task_object.contract_address,
                                     task_object.abi_type,
                                     task_object.function,
                                     task_object.args,
                                     task_object.kwargs,
                                     task_object.gas_limit,
                                     task_object.id))

        elif task_object.type == 'DEPLOY_CONTRACT':
            print(f'Starting Deploy {task_object.contract_name} Contract Transaction for {task_uuid}.' + attempt_info)
            chain1 = signature(utils.eth_endpoint('_process_deploy_contract_transaction'),
                               args=(transaction_obj.id,
                                     task_object.contract_name,
                                     task_object.args,
                                     task_object.kwargs,
                                     task_object.gas_limit,
                                     task_object.id))
        else:
            raise Exception(f"Task type {task_object.type} not recognised")

        chain2 = signature(utils.eth_endpoint('_check_transaction_response'))

        error_callback = signature(utils.eth_endpoint('_log_error'), args=(transaction_obj.id,))

        return chain([chain1, chain2]).on_error(error_callback).delay()

    def get_signing_wallet_object(self, signing_address, encrypted_private_key):
        if signing_address:

            signing_wallet_obj = self.persistence_interface.get_wallet_by_address(signing_address)

            if signing_wallet_obj is None:
                raise Exception('Address {} not found'.format(signing_address))

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

        if not getattr(exc, 'is_logged', False):
            print("LOGGING")
            self.persistence_interface.update_transaction_data(transaction_id, data)
        else:
            print("NOT LOGGING")

    def new_transaction_attempt(self, task):
        number_of_attempts_this_round = abs(
            len(task.transactions) - self.task_max_retries * (task.previous_invocations or 0)
        )
        if number_of_attempts_this_round >= self.task_max_retries:
            print(f"Maximum retries exceeded for task {task.uuid}")

            if task.status_text != 'SUCCESS':
                self.persistence_interface.set_task_status_text(task, 'FAILED')

            raise TaskRetriesExceededError

        else:
            # TODO: Convert to task_runner
            signature(utils.eth_endpoint('_attempt_transaction'),
                      args=(task.uuid,)).apply_async(
                countdown=RETRY_TRANSACTION_BASE_TIME * 4 ** number_of_attempts_this_round
            )


    def get_serialised_task_from_uuid(self, uuid):
        return self.persistence_interface.get_serialised_task_from_uuid(uuid)

    def call_contract_function(self,
                               contract_address: str, abi_type: str, function_name: str,
                               args: Optional[tuple] = None, kwargs: Optional[dict] = None,
                               signing_address: Optional[str] = None) -> Any:
        """
        The main call entrypoint for the transaction. This task completes quickly,
        so can be called synchronously.

        :param contract_address: address of the contract for the function
        :param abi_type: the type of ABI for the contract being called
        :param function_name: name of the function
        :param args: arguments for the function
        :param kwargs: keyword arguments for the function
        :return: the result of the contract call
        """

        args = args or tuple()
        if not isinstance(args, (list, tuple)):
            args = [args]

        kwargs = kwargs or dict()

        function_list = self.registry.get_contract_function(contract_address, function_name, abi_type)

        function = function_list(*args, **kwargs)

        txn_meta = {'gasPrice': self.get_gas_price()}

        if signing_address:
            txn_meta['from'] = signing_address

        call_data = function.call(txn_meta)

        if isinstance(call_data, bytes):
            return call_data.rstrip(b'\x00').decode()

        return call_data

    def transact_with_contract_function(
            self,
            uuid: UUID,
            contract_address: str, abi_type: str, function_name: str,
            args: Optional[tuple] = None, kwargs: Optional[dict] = None,
            signing_address: Optional[str] = None, encrypted_private_key: Optional[str]=None,
            gas_limit: Optional[int] = None,
            prior_tasks: Optional[UUIDList] = None
    ):
        """
        The main transaction entrypoint for the processor.
        :param uuid: the celery generated uuid for the task
        :param contract_address: the address of the contract for the function
        :param abi_type: the type of ABI for the contract being called
        :param function_name: name of the function
        :param args: arguments for the function
        :param kwargs: keyword arguments for the function
        :param signing_address: address of the wallet signing the txn
        :param encrypted_private_key: private key of the wallet making the transaction, encrypted using key from settings
        :param gas_limit: limit on the amount of gas txn can use. Overrides system default
        :param prior_tasks: a list of task uuids that must succeed before this task will be attempted
        :return: task_id
        """

        signing_wallet_obj = self.get_signing_wallet_object(signing_address, encrypted_private_key)

        task = self.persistence_interface.create_function_task(uuid,
                                                               signing_wallet_obj,
                                                               contract_address, abi_type,
                                                            function_name, args, kwargs,
                                                               gas_limit, prior_tasks)

        # Attempt Create Async Transaction
        signature(utils.eth_endpoint('_attempt_transaction'), args=(task.uuid,)).delay()

    def send_eth(self,
                 uuid: UUID,
                 amount_wei: int,
                 recipient_address: str,
                 signing_address: Optional[str] = None, encrypted_private_key: Optional[str] = None,
                 prior_tasks: Optional[UUIDList] = None,
                 posterior_tasks: Optional[UUIDList] = None):
        """
        The main entrypoint sending eth.

        :param uuid: the celery generated uuid for the task
        :param amount_wei: the amount in WEI to send
        :param recipient_address: the recipient address
        :param signing_address: address of the wallet signing the txn
        :param encrypted_private_key: private key of the wallet making the transaction, encrypted using key from settings
        :param prior_tasks: a list of task uuids that must succeed before this task will be attempted
        :param posterior_tasks: a uuid list of tasks for which this task must succeed before they will be attempted
        :return: task_id
        """

        signing_wallet_obj = self.get_signing_wallet_object(signing_address, encrypted_private_key)

        task = self.persistence_interface.create_send_eth_task(uuid,
                                                               signing_wallet_obj,
                                                               recipient_address, amount_wei,
                                                               prior_tasks,
                                                               posterior_tasks)

        # Attempt Create Async Transaction
        signature(utils.eth_endpoint('_attempt_transaction'), args=(task.uuid,)).delay()

    def deploy_contract(
            self,
            uuid: UUID,
            contract_name: str,
            args: Optional[tuple] = None, kwargs: Optional[dict] = None,
            signing_address: Optional[str] = None, encrypted_private_key: Optional[str]=None,
            gas_limit: Optional[int] = None,
            prior_tasks: Optional[UUIDList] = None
    ):
        """
        The main deploy contract entrypoint for the processor.

        :param uuid: the celery generated uuid for the task
        :param contract_name: System will attempt to fetched abi and bytecode from this
        :param args: arguments for the constructor
        :param kwargs: keyword arguments for the constructor
        :param signing_address: address of the wallet signing the txn
        :param encrypted_private_key: private key of the wallet making the transaction, encrypted using key from settings
        :param gas_limit: limit on the amount of gas txn can use. Overrides system default
        :param prior_tasks: a list of task uuid that must succeed before this task will be attempted
        """

        signing_wallet_obj = self.get_signing_wallet_object(signing_address, encrypted_private_key)

        task = self.persistence_interface.create_deploy_contract_task(uuid,
                                                                      signing_wallet_obj,
                                                                      contract_name,
                                                                      args, kwargs,
                                                                      gas_limit,
                                                                      prior_tasks)

        # Attempt Create Async Transaction
        signature(utils.eth_endpoint('_attempt_transaction'), args=(task.uuid,)).delay()

    def retry_task(self, uuid: UUID):
        task = self.persistence_interface.get_task_from_uuid(uuid)

        self._retry_task(task)

    def retry_failed(self):

        failed_tasks = self.persistence_interface.get_failed_tasks()
        pending_tasks = self.persistence_interface.get_pending_tasks()

        print(f"{len(failed_tasks)} tasks currently with failed state")
        print(f"{len(pending_tasks)} tasks currently pending")

        for task in failed_tasks:
            self._retry_task(task)

        return {
            'failed_count': len(failed_tasks),
            'pending_count': len(pending_tasks)
        }

    def _retry_task(self, task):
        self.persistence_interface.increment_task_invokations(task)
        signature(utils.eth_endpoint('_attempt_transaction'), args=(task.uuid,)).delay()

    def __init__(self,
                 ethereum_chain_id,
                 w3,
                 gas_price_gwei,
                 gas_limit,
                 persistence_interface,
                 task_max_retries=3):

            self.registry = ContractRegistry(w3)

            self.ethereum_chain_id = int(ethereum_chain_id) if ethereum_chain_id else None
            self.w3 = w3

            self.gas_price = self.w3.toWei(gas_price_gwei, 'gwei')
            self.gas_limit = gas_limit
            self.transaction_max_value = self.gas_price * self.gas_limit

            self.persistence_interface = persistence_interface

            self.task_max_retries = task_max_retries


