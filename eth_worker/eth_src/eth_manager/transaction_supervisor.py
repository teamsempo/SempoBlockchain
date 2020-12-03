import datetime

import celery_utils
import celery_app 
from celery import chain, signature
from celery_utils import eth_endpoint

import config

from exceptions import TaskRetriesExceededError
from eth_manager.eth_transaction_processor import EthTransactionProcessor

RETRY_TRANSACTION_BASE_TIME = 2
CHECK_TRANSACTION_BASE_TIME = 2
CHECK_TRANSACTION_RETRIES_TIME_LIMIT = 4

class TransactionSupervisor(object):
    """
        Takes tasks from the task manager.
        Is in charge of telling the EthTransactionProcessor what transactions to attempt.
        Also checks the results from the EthTransactionProcessor (via check_transaction_response) and tells
        the processor to try again as appropriate. #MiddleManagement
        Doesn't know about any eth specific concepts, so in theory EthTransactionProcessor should be somewhat easy
        to swap out for a different type of processor by changing the where the processor tasks are sent
    """

    def check_transaction_response(self, celery_task, transaction_id):
        def transaction_response_countdown():
            t = lambda retries: CHECK_TRANSACTION_BASE_TIME * 2 ** retries

            # If the system has been longer than the max retry period
            # if previous_result:
            #     submitted_at = datetime.strptime(previous_result['submitted_date'], "%Y-%m-%d %H:%M:%S.%f")
            #     if (datetime.utcnow() - submitted_at).total_seconds() > CHECK_TRANSACTION_RETRIES_TIME_LIMIT:
            #         if self.request.retries != self.max_retries:
            #             self.request.retries = self.max_retries - 1
            #
            #         return 0

            return t(celery_task.request.retries)

        try:

            result = self.processor.get_transaction_status(transaction_id)

            self.persistence.update_transaction_data(transaction_id, result)

            transaction_object = self.persistence.get_transaction(transaction_id)

            task = transaction_object.task

            status = result.get('status')

            print(f'Status for transaction {transaction_object.id} of task UUID {task.uuid} is:'
            f'\n {status}')
            if status == 'SUCCESS':

                unstarted_posteriors = self.persistence.get_unstarted_posteriors(task.uuid)

                for dep_task in unstarted_posteriors:
                    print('Starting posterior task: {}'.format(dep_task.uuid))
                    self.queue_attempt_transaction(dep_task.uuid)

                self.persistence.set_task_status_text(task, 'SUCCESS')

            if status == 'PENDING':
                raise Exception("Need Retry")

            if status == 'FAILED':
                self.new_transaction_attempt(task)

        except TaskRetriesExceededError as e:
            pass

        except Exception as e:
            print(e)
            celery_task.retry(countdown=transaction_response_countdown())

    def attempt_transaction(self, task_uuid):

        task = self.persistence.get_task_from_uuid(task_uuid)

        unsatisfied_prior_tasks = self.persistence.get_unsatisfied_prior_tasks(task_uuid)
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
                return self.persistence.create_blockchain_transaction(task.uuid)
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
            txn_sig = self.processor.sigs.process_send_eth_transaction(
                transaction_id,
                task.recipient_address,
                transfer_amount,
                task.id
            )

        elif task.type == 'FUNCTION':
            print(f'Starting {task.function} Transaction for {task.uuid}.' + attempt_info)
            txn_sig = self.processor.sigs.process_function_transaction(
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
            txn_sig = self.processor.sigs.process_deploy_contract_transaction(
                transaction_id,
                task.contract_name,
                task.args,
                task.kwargs,
                task.gas_limit,
                task.id
            )
        else:
            raise Exception(f"Task type {task.type} not recognised")

        check_response_sig = self.sigs.check_transaction_response()
        error_callback_sig = self.sigs.handle_error(transaction_id)

        return chain([txn_sig, check_response_sig]).on_error(error_callback_sig)

    def _topup_if_required(self, wallet, posterior_task_uuid):

        balance = self.processor.get_wallet_balance(wallet)

        wei_topup_threshold = wallet.wei_topup_threshold
        wei_target_balance = wallet.wei_target_balance or 0

        if balance <= wei_topup_threshold and wei_target_balance > balance:
            task_uuid = self.queue_send_eth(
                signing_address=celery_app.chain_config['MASTER_WALLET_ADDRESS'],
                amount_wei=wei_target_balance - balance,
                recipient_address=wallet.address,
                prior_tasks=[],
                posterior_tasks=[posterior_task_uuid]
            )

            self.persistence.set_wallet_last_topup_task_uuid(wallet.address, task_uuid)

            return task_uuid

        return None

    def handle_error(self, request, exc, traceback, transaction_id):
        self.log_error(request, exc, traceback, transaction_id)

        transaction = self.persistence.get_transaction(transaction_id)
        task = transaction.task

        try:
            self.new_transaction_attempt(task)
        except:
            pass

    def log_error(self, request, exc, traceback, transaction_id):
        data = {
            'error': type(exc).__name__,
            'message': str(exc.args[0]),
            'status': 'FAILED'
        }

        self.persistence.update_transaction_data(transaction_id, data)

    def new_transaction_attempt(self, task):
        number_of_attempts_this_round = abs(
            len(task.transactions) - self.task_max_retries * (task.previous_invocations or 0)
        )
        if number_of_attempts_this_round >= self.task_max_retries:
            print(f"Maximum retries exceeded for task {task.uuid}")

            if task.status_text != 'SUCCESS':
                self.persistence.set_task_status_text(task, 'FAILED')

            raise TaskRetriesExceededError

        else:
            self.queue_attempt_transaction(
                task.uuid,
                countdown=RETRY_TRANSACTION_BASE_TIME * 4 ** number_of_attempts_this_round
            )

    def queue_attempt_transaction(self, task_uuid, countdown=0):
        return celery_utils.queue_sig(self.sigs.attempt_transaction(task_uuid), countdown)

    def queue_send_eth(
            self,
            signing_address,
            amount_wei,
            recipient_address,
            prior_tasks,
            posterior_tasks,
    ):
        """
        This is a slightly smelly special case where the transaction supervisor needs to call the higher-level
        task manager to get a send_eth task created for topup purposes.
        """
        sig = signature(eth_endpoint('send_eth'),
                        kwargs={
                            'signing_address': signing_address,
                            'amount_wei': amount_wei,
                            'recipient_address': recipient_address,
                            'prior_tasks': prior_tasks,
                            'posterior_tasks': posterior_tasks
                        })

        return celery_utils.queue_sig(sig)

    def __init__(
            self,
            red,
            persistence,
            processor: EthTransactionProcessor,
            task_max_retries=3
    ):

        self.red = red
        self.persistence = persistence
        self.processor = processor
        self.task_max_retries = task_max_retries
        self.sigs = SigGenerators()

class SigGenerators(object):

    def attempt_transaction(self, task_uuid):
        return signature(eth_endpoint('attempt_transaction'), kwargs={'task_uuid': task_uuid})

    def check_transaction_response(self):
        return signature(eth_endpoint('_check_transaction_response'))

    def handle_error(self, transaction_id):
        return signature(eth_endpoint('_handle_error'), args=(transaction_id,))