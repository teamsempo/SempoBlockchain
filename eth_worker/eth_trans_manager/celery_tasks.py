import celery
import config
from eth_trans_manager.models import session
from eth_trans_manager import celery_app, blockchain_processor

class SqlAlchemyTask(celery.Task):
    """An abstract Celery Task that ensures that the connection the the
    database is closed on task completion"""
    abstract = True

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        session.remove()

@celery_app.task(base=SqlAlchemyTask, bind=True, max_retries=3, soft_time_limit=300)
def create_account(self):
    account = blockchain_processor.persistence_model.create_account()
    return account.address

@celery_app.task(base=SqlAlchemyTask, bind=True, max_retries=3, soft_time_limit=300)
def register_contract(self, contract_address, abi, contract_name=None, require_name_matches=False):
    blockchain_processor.registry.register_contract(
        contract_address, abi, contract_name, require_name_matches
    )

@celery_app.task(base=SqlAlchemyTask, bind=True, max_retries=3, soft_time_limit=300)
def call_contract_function(self, contract, function, args=None, kwargs=None):
    return blockchain_processor.call_contract_function(contract, function, args, kwargs)

@celery_app.task(base=SqlAlchemyTask, bind=True, max_retries=3, soft_time_limit=300)
def transact_with_contract_function(self, encrypted_private_key, contract, function, args=None, kwargs=None, dependent_on_tasks=None):
    return blockchain_processor.transact_with_contract_function(encrypted_private_key, contract, function, args, kwargs, dependent_on_tasks)

@celery_app.task(base=SqlAlchemyTask, bind=True, max_retries=3, soft_time_limit=300)
def _attempt_transaction(self, transaction_id, contract, function, args=None, kwargs=None):
    return blockchain_processor.attempt_transaction(transaction_id, contract, function, args, kwargs)

@celery_app.task(base=SqlAlchemyTask, bind=True, max_retries=3, soft_time_limit=300)
def _process_function_transaction(self, transaction_id, contract, function, args=None, kwargs=None):
    return blockchain_processor.process_function_transaction(transaction_id, contract, function, args, kwargs)

@celery_app.task(base=SqlAlchemyTask, bind=True, max_retries=config.ETH_CHECK_TRANSACTION_RETRIES, soft_time_limit=300)
def _check_transaction_response(self, transaction_id):
    ETH_CHECK_TRANSACTION_BASE_TIME = 2
    ETH_CHECK_TRANSACTION_RETRIES_TIME_LIMIT = 4


    def transaction_response_countdown():
        t = lambda retries: ETH_CHECK_TRANSACTION_BASE_TIME*2**retries

        # If the system has been longer than the max retry period
        # if previous_result:
        #     submitted_at = datetime.strptime(previous_result['submitted_date'], "%Y-%m-%d %H:%M:%S.%f")
        #     if (datetime.utcnow() - submitted_at).total_seconds() > ETH_CHECK_TRANSACTION_RETRIES_TIME_LIMIT:
        #         if self.request.retries != self.max_retries:
        #             self.request.retries = self.max_retries - 1
        #
        #         return 0

        return t(self.request.retries)

    try:
        success = blockchain_processor.check_transaction_response(transaction_id)

        if not success:
            # We only get here from a next block condition, so reset the retry counter
            self.request.retries = 0
            self.retry(countdown=transaction_response_countdown())

    except Exception as e:
        print(e)
        self.retry(countdown=transaction_response_countdown())

@celery_app.task(base=SqlAlchemyTask)
def _log_error(request, exc, traceback, transaction_id):
    blockchain_processor.log_error(request, exc, traceback, transaction_id)