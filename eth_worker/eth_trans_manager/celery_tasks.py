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
def transact_with_contract_function(self, encrypted_private_key, contract, function, args=None, kwargs=None):
    return blockchain_processor.transact_with_contract_function(encrypted_private_key, contract, function, args, kwargs)


@celery_app.task(base=SqlAlchemyTask, bind=True, max_retries=3, soft_time_limit=300)
def _attempt_transaction(self, transaction_id, contract, function, args=None, kwargs=None):
    return blockchain_processor.attempt_transaction(transaction_id, contract, function, args, kwargs)

@celery_app.task(base=SqlAlchemyTask, bind=True, max_retries=3, soft_time_limit=300)
def _process_function_transaction(self, transaction_id, contract, function, args=None, kwargs=None):
    return blockchain_processor.process_function_transaction(transaction_id, contract, function, args, kwargs)

@celery_app.task(base=SqlAlchemyTask, bind=True, max_retries=config.ETH_CHECK_TRANSACTION_RETRIES, soft_time_limit=300)
def _create_transaction_response(self, transaction_id):
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
        blockchain_processor.create_transaction_response(transaction_id)

    except Exception as e:
        print(e)
        self.retry(countdown=transaction_response_countdown())

@celery_app.task(base=SqlAlchemyTask)
def _log_error(request, exc, traceback, transaction_id):
    blockchain_processor.log_error(request, exc, traceback, transaction_id)