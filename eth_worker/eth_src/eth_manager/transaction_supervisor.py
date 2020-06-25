import datetime

from celery import chain

import config
from celery_dispatchers.regular import queue_attempt_transaction, sig_process_send_eth_transaction, \
    sig_process_function_transaction, sig_process_deploy_contract_transaction, sig_check_transaction_response, \
    sig_log_error, queue_send_eth
from eth_manager.transaction_processor import ETH_CHECK_TRANSACTION_BASE_TIME, RETRY_TRANSACTION_BASE_TIME
from exceptions import TaskRetriesExceededError


class TransactionSupervisor(object):
    """
        Takes tasks from the task manager.
        Is in charge of telling the TransactionProcessor what transactions to attempt.
        Also checks the results from the TransactionProcessor (via check_transaction_response) and tells
        the processor to try again as appropriate. #MiddleManagement
    """

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
                 w3,
                 red,
                 persistence_module,
                 task_max_retries=3):

            self.w3 = w3
            self.red = red
            self.persistence_interface = persistence_module
            self.task_max_retries = task_max_retries