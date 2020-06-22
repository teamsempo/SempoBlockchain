from typing import Optional, Any

import datetime

from celery import chain

import requests

import config
from celery_dispatchers.regular import (
    queue_attempt_transaction,
    queue_send_eth,
    sig_process_send_eth_transaction,
    sig_process_function_transaction,
    sig_process_deploy_contract_transaction,
    sig_check_transaction_response,
    sig_log_error
)
from exceptions import PreBlockchainError, TaskRetriesExceededError
from eth_manager.contract_registry.contract_registry import ContractRegistry

RETRY_TRANSACTION_BASE_TIME = 2
ETH_CHECK_TRANSACTION_BASE_TIME = 2
ETH_CHECK_TRANSACTION_RETRIES_TIME_LIMIT = 4


class TransactionProcessor(object):

    def _shape_args(self, args):
        args = args or tuple()
        if not isinstance(args, (list, tuple)):
            args = [args]
        return [self._typecast_argument(a) for a in args]

    def _shape_kwargs(self, kwargs):
        kwargs = kwargs or dict()
        return {k: self._typecast_argument(v) for k, v in kwargs.items()}

    def _typecast_argument(self, argument):
        if isinstance(argument, dict) and argument.get('type') == 'bytes':
            return argument.get('data').encode()
        return argument

    def call_contract_function(self,
                               contract_address: str, abi_type: str, function_name: str,
                               args: Optional[tuple] = None, kwargs: Optional[dict] = None,
                               signing_address: Optional[str] = None) -> Any:
        """
        The main call entrypoint for the transaction. This task completes quickly and doesn't mutate any state, so this
        directly goes to the blockchain rather than going via the task queue.

        :param contract_address: address of the contract for the function
        :param abi_type: the type of ABI for the contract being called
        :param function_name: name of the function
        :param args: arguments for the function
        :param kwargs: keyword arguments for the function
        :param signing_address: required when the function is dependent on the signing address
        :return: the result of the contract call
        """

        args = self._shape_args(args)
        kwargs = self._shape_kwargs(kwargs)

        function_list = self.registry.get_contract_function(contract_address, function_name, abi_type)

        function = function_list(*args, **kwargs)

        txn_meta = {'gasPrice': self._get_gas_price()}

        if signing_address:
            txn_meta['from'] = signing_address

        call_data = function.call(txn_meta)

        if isinstance(call_data, bytes):
            return call_data.rstrip(b'\x00').decode()

        return call_data

    def process_send_eth_transaction(self, transaction_id,
                                     recipient_address, amount, task_id=None):

        partial_txn_dict = {
            'to': recipient_address,
            'value': amount
        }

        print(f'\n##Tx {transaction_id}, task {task_id}: Sending Eth \n'
              f'to: {recipient_address} \n'
              f'amount: {amount}')

        return self._process_transaction(transaction_id, partial_txn_dict=partial_txn_dict, gas_limit=100000)

    def process_function_transaction(self, transaction_id, contract_address, abi_type,
                                     function_name, args=None, kwargs=None, gas_limit=None, task_id=None):

        args = self._shape_args(args)
        kwargs = self._shape_kwargs(kwargs)

        print(f'\n##Tx {transaction_id}, task {task_id}: Transacting with Function {function_name} \n'
              f'Args: {args} \n'
              f'Kwargs: {kwargs}')

        fn = self.registry.get_contract_function(contract_address, function_name, abi_type)

        bound_function = fn(*args, **kwargs)

        return self._process_transaction(transaction_id, unbuilt_transaction=bound_function, gas_limit=gas_limit)

    def process_deploy_contract_transaction(self, transaction_id, contract_name,
                                            args=None, kwargs=None, gas_limit=None, task_id=None):

        args = self._shape_args(args)
        kwargs = self._shape_kwargs(kwargs)

        print(f'\n##Tx {transaction_id}, task {task_id}: Deploying Contract {contract_name} \n'
              f'Args: {args} \n'
              f'Kwargs: {kwargs}')

        contract = self.registry.get_compiled_contract(contract_name)

        constructor = contract.constructor(*args, **kwargs)

        return self._process_transaction(transaction_id, unbuilt_transaction=constructor, gas_limit=gas_limit)

    def _process_transaction(self,
                             transaction_id,
                             unbuilt_transaction=None,
                             partial_txn_dict=None,
                             gas_limit=None,
                             gas_price=None):
        try:

            signing_wallet_obj = self.persistence_interface.get_transaction_signing_wallet(transaction_id)

            metadata = self._compile_transaction_metadata(
                signing_wallet_obj,
                transaction_id,
                unbuilt_transaction,
                gas_limit,
                gas_price
            )

            built_txn = self._construct_full_txn_dict(
                metadata,
                partial_txn_dict,
                unbuilt_transaction
            )

            signed_transaction = self.w3.eth.account.sign_transaction(
                built_txn,
                private_key=signing_wallet_obj.private_key
            )

            self._send_signed_transaction(signed_transaction, transaction_id)

            # If we've made it this far, the nonce will(?) be consumed
            transaction_data = {
                'hash': signed_transaction.hash.hex(),
                'nonce': metadata['nonce'],
                'submitted_date': str(datetime.datetime.utcnow()),
                'nonce_consumed': True
            }

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

    def _calculate_nonce(self, signing_wallet_obj, transaction_id):
        network_nonce = self.w3.eth.getTransactionCount(signing_wallet_obj.address, block_identifier='pending')

        return self.persistence_interface.locked_claim_transaction_nonce(
            network_nonce, signing_wallet_obj.id, transaction_id
        )

    def _compile_transaction_metadata(
            self,
            signing_wallet_obj,
            transaction_id,
            unbuilt_transaction=None,
            gas_limit=None,
            gas_price=None):

        chain_id = self.ethereum_chain_id
        gas_price = gas_price or self.gas_price_wei

        if gas_limit:
            gas = gas_limit
        else:
            if not unbuilt_transaction:
                raise Exception("Must specify gas limit or an unbuilt transaction")
            try:
                gas = unbuilt_transaction.estimateGas({
                    'from': signing_wallet_obj.address,
                    'gasPrice': gas_price
                })
            except ValueError as e:
                print("Estimate Gas Failed. Remedy by specifying gas limit.")

                raise e

        nonce = self._calculate_nonce(signing_wallet_obj, transaction_id)

        metadata = {
            'gas': gas,
            'gasPrice': gas_price,
            'nonce': nonce
        }

        if chain_id:
            metadata['chainId'] = chain_id

        return metadata

    def _construct_full_txn_dict(self, metadata, partial_txn_dict=None, unbuilt_transaction=None):

        if not partial_txn_dict and not unbuilt_transaction:
            raise Exception("Must provide partial_txn_dict and/or unbuilt_transaction data")

        if not partial_txn_dict:
            partial_txn_dict = {}

        txn_dict = {**metadata, **partial_txn_dict}

        if unbuilt_transaction:
            txn_dict =  unbuilt_transaction.buildTransaction(txn_dict)

        return txn_dict

    def _send_signed_transaction(self, signed_transaction, transaction_id):
        try:

            self.w3.eth.sendRawTransaction(signed_transaction.rawTransaction)

        except ValueError as e:
            message = f'Transaction {transaction_id}: {str(e)}'
            exc = PreBlockchainError(message, False)
            self.log_error(None, exc, None, transaction_id)

            raise PreBlockchainError(message, True)

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

                unstarted_posteriors = self.persistence_interface.get_unstarted_posteriors(task.uuid)

                for dep_task in unstarted_posteriors:
                    print('Starting posterior task: {}'.format(dep_task.uuid))
                    queue_attempt_transaction(dep_task.uuid)

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

        if tx_receipt is None:
            return {'status': 'PENDING'}

        mined_date = str(datetime.datetime.utcnow())

        if tx_receipt.blockNumber is None:
            return {'status': 'PENDING', 'message': 'Next Block'}

        if tx_receipt.status == 1:

            return {
                'status': 'SUCCESS',
                'block': tx_receipt.blockNumber,
                'contract_address': tx_receipt.contractAddress,
                'mined_date': mined_date
            }

        else:
           return {
               'status': 'FAILED',
               'error': 'Blockchain Error',
               'block': tx_receipt.blockNumber,
               'mined_date': mined_date
           }

    def attempt_transaction(self, task_uuid):

        task = self.persistence_interface.get_task_from_uuid(task_uuid)

        unsatisfied_prior_tasks = self.persistence_interface.get_unsatisfied_prior_tasks(task_uuid)
        if len(unsatisfied_prior_tasks) > 0:
            print('Skipping {}: prior tasks {} unsatisfied'.format(
                task.id,
                [f'{u.id} ({u.uuid})' for u in unsatisfied_prior_tasks]))
            return

        topup_uuid = self._topup_if_required(task.signing_wallet, task_uuid)
        if topup_uuid:
            print(f'Skipping {task.id}: Topup required')
            return

        transaction = self._create_transaction_with_lock(task)

        if not transaction:
            return

        return self._construct_attempt_transaction_chain(task, transaction.id).delay()

    def _create_transaction_with_lock(self, task):
        # This is designed to ensure that we don't have two transactions running for the same task
        # at the same time. Under normal conditions this doesn't happen, but the 'retry failed transactions' can
        # get us there if it's called twice in quick succession. We use a mutex over the next lines
        # to prevent two processes both passing the 'current_status' test and then creating a transaction

        have_lock = False
        lock = self.red.lock(f'TaskID-{task.id}', timeout=10)
        try:
            have_lock = lock.acquire(blocking_timeout=1)
            if have_lock:
                current_status = task.status
                if current_status in ['SUCCESS', 'PENDING']:
                    print(f'Skipping {task.id}: task status is currently {current_status}')
                    return None
                return self.persistence_interface.create_blockchain_transaction(task.uuid)
            else:
                print(f'Skipping {task.id}: Failed to aquire lock')
                return None

        finally:
            if have_lock:
                lock.release()

    def _construct_attempt_transaction_chain(self, task, transaction_id):

        number_of_attempts = len(task.transactions)

        attempt_info = f'\nAttempt number: {number_of_attempts} ' \
                       f' for invocation round: {task.previous_invocations + 1}'

        if task.type == 'SEND_ETH':

            transfer_amount = int(task.amount)

            print(f'Starting Send Eth Transaction for {task.uuid}.' + attempt_info)
            txn_sig = sig_process_send_eth_transaction(
                transaction_id,
                task.recipient_address,
                transfer_amount,
                task.id
            )

        elif task.type == 'FUNCTION':
            print(f'Starting {task.function} Transaction for {task.uuid}.' + attempt_info)
            txn_sig = sig_process_function_transaction(
                transaction_id,
                task.contract_address,
                task.abi_type,
                task.function,
                task.args,
                task.kwargs,
                task.gas_limit,
                task.id
            )

        elif task.type == 'DEPLOY_CONTRACT':
            print(f'Starting Deploy {task.contract_name} Contract Transaction for {task.uuid}.' + attempt_info)
            txn_sig = sig_process_deploy_contract_transaction(
                transaction_id,
                task.contract_name,
                task.args,
                task.kwargs,
                task.gas_limit,
                task.id
            )
        else:
            raise Exception(f"Task type {task.type} not recognised")

        check_response_sig = sig_check_transaction_response()

        error_callback_sig = sig_log_error(transaction_id)

        return chain([txn_sig, check_response_sig]).on_error(error_callback_sig)

    def _get_gas_price(self, target_transaction_time=None):

        if not target_transaction_time:
            target_transaction_time = config.ETH_TARGET_TRANSACTION_TIME

        try:
            gas_price_req = requests.get(config.ETH_GAS_PRICE_PROVIDER + '/price',
                                         params={'max_wait_seconds': target_transaction_time}).json()

            gas_price = min(gas_price_req['gas_price'], self.gas_price_wei)

            print('gas price: {}'.format(gas_price))

        except Exception as e:
            gas_price = self.gas_price_wei

        return gas_price

    def _topup_if_required(self, wallet, posterior_task_uuid):
        balance = self.w3.eth.getBalance(wallet.address)

        wei_topup_threshold = wallet.wei_topup_threshold
        wei_target_balance = wallet.wei_target_balance or 0

        if balance <= wei_topup_threshold and wei_target_balance > balance:
            task_uuid = queue_send_eth(
                signing_address=config.MASTER_WALLET_ADDRESS,
                amount_wei=wei_target_balance - balance,
                recipient_address=wallet.address,
                prior_tasks=[],
                posterior_tasks=[posterior_task_uuid]
            )

            self.persistence_interface.set_wallet_last_topup_task_uuid(wallet.address, task_uuid)

            return task_uuid

        return None

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
            queue_attempt_transaction(
                task.uuid,
                countdown=RETRY_TRANSACTION_BASE_TIME * 4 ** number_of_attempts_this_round
            )


    def get_serialised_task_from_uuid(self, uuid):
        return self.persistence_interface.get_serialised_task_from_uuid(uuid)


    def __init__(self,
                 ethereum_chain_id,
                 w3,
                 red,
                 gas_price_wei,
                 gas_limit,
                 persistence_module,
                 task_max_retries=3):

            self.registry = ContractRegistry(w3)

            self.ethereum_chain_id = int(ethereum_chain_id) if ethereum_chain_id else None

            self.red = red

            self.w3 = w3

            self.gas_price_wei = gas_price_wei
            self.gas_limit = gas_limit
            self.transaction_max_value = self.gas_price_wei * self.gas_limit

            self.persistence_interface = persistence_module

            self.task_max_retries = task_max_retries


