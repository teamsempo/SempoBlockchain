import celery
import config
import eth_manager.task_interfaces.composite
from sql_persistence.models import session
from eth_manager import celery_app, blockchain_processor, persistence_interface
from functools import wraps

class SqlAlchemyTask(celery.Task):
    """An abstract Celery Task that ensures that the connection the the
    database is closed on task completion"""
    abstract = True

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        session.remove()


base_task_config = {
    'base': SqlAlchemyTask,
    'bind': True,
    'autoretry_for': (Exception,),
    'max_retries': 3,
    'soft_time_limit': 300,
    'retry_backoff': True
}

no_retry_config = {
    **base_task_config,
    'max_retries': 0
}

processor_task_config = {
    **base_task_config,
    'max_retries': 0,
    'queue': 'processor'
}


@celery_app.task(**base_task_config)
def deploy_exchange_network(self, deploying_address):
    return eth_manager.task_interfaces.composite.deploy_exchange_network(deploying_address)


@celery_app.task(**base_task_config)
def deploy_and_fund_reserve_token(self, deploying_address, name, symbol, fund_amount_wei):
    return eth_manager.task_interfaces.composite.deploy_and_fund_reserve_token(
        deploying_address,
        name, symbol, fund_amount_wei)


@celery_app.task(**base_task_config)
def deploy_smart_token(self, deploying_address,
                       name, symbol, decimals,
                       reserve_deposit_wei,
                       issue_amount_wei,
                       contract_registry_address,
                       reserve_token_address,
                       reserve_ratio_ppm):

    return eth_manager.task_interfaces.composite.deploy_smart_token(
        deploying_address,
        name, symbol, decimals,
        reserve_deposit_wei,
        issue_amount_wei,
        contract_registry_address,
        reserve_token_address,
        reserve_ratio_ppm)


@celery_app.task(**base_task_config)
def create_new_blockchain_wallet(self, wei_target_balance=0, wei_topup_threshold=0, private_key=None):
    wallet = persistence_interface.create_new_blockchain_wallet(wei_target_balance=wei_target_balance,
                                                                wei_topup_threshold=wei_topup_threshold,
                                                                private_key=private_key)
    return wallet.address


@celery_app.task(**base_task_config)
def topup_wallets(self):
    eth_manager.task_interfaces.composite.topup_wallets()


# Set retry attempts to zero since beat will retry shortly anyway
@celery_app.task(**no_retry_config)
def topup_wallet_if_required(self, address):
    return eth_manager.task_interfaces.composite.topup_if_required(address)


@celery_app.task(**base_task_config)
def register_contract(self, contract_address, abi, contract_name=None, require_name_matches=False):
    return blockchain_processor.registry.register_contract(
        contract_address, abi, contract_name, require_name_matches
    )


@celery_app.task(**base_task_config)
def call_contract_function(self, contract_address, function, abi_type=None, args=None, kwargs=None,
                           signing_address=None):
    return blockchain_processor.call_contract_function(contract_address, abi_type, function, args, kwargs,
                                                       signing_address)


@celery_app.task(**base_task_config)
def transact_with_contract_function(self, contract_address, function,  abi_type=None, args=None, kwargs=None,
                                    signing_address=None, encrypted_private_key=None,
                                    gas_limit=None, dependent_on_tasks=None):

    return blockchain_processor.transact_with_contract_function(contract_address, abi_type, function, args, kwargs,
                                                                signing_address, encrypted_private_key,
                                                                gas_limit, dependent_on_tasks)


@celery_app.task(**base_task_config)
def deploy_contract(self, contract_name, args=None, kwargs=None,
                    signing_address=None, encrypted_private_key=None,
                    gas_limit=None, dependent_on_tasks=None):

    return blockchain_processor.deploy_contract(contract_name, args, kwargs,
                                                signing_address, encrypted_private_key,
                                                gas_limit, dependent_on_tasks)


@celery_app.task(**base_task_config)
def send_eth(self, amount_wei, recipient_address,
             signing_address=None, encrypted_private_key=None,
             dependent_on_tasks=None):

    return blockchain_processor.send_eth(amount_wei, recipient_address,
                                         signing_address, encrypted_private_key,
                                         dependent_on_tasks)


@celery_app.task(**base_task_config)
def get_task(self, task_id):
    return blockchain_processor.get_serialised_task_from_id(task_id)


@celery_app.task(**base_task_config)
def _attempt_transaction(self, task_id):
    return blockchain_processor.attempt_transaction(task_id)


@celery_app.task(**processor_task_config)
def _process_send_eth_transaction(self, transaction_id, recipient_address, amount, task_id=None):
    return blockchain_processor.process_send_eth_transaction(transaction_id, recipient_address, amount, task_id)


@celery_app.task(**processor_task_config)
def _process_function_transaction(self, transaction_id, contract_address, abi_type,
                                  function, args=None, kwargs=None,  gas_limit=None, task_id=None):

    return blockchain_processor.process_function_transaction(transaction_id, contract_address, abi_type,
                                                             function, args, kwargs, gas_limit, task_id)


@celery_app.task(**processor_task_config)
def _process_deploy_contract_transaction(self, transaction_id, contract_name,
                                         args=None, kwargs=None,  gas_limit=None, task_id=None):

    return blockchain_processor.process_deploy_contract_transaction(transaction_id, contract_name,
                                                                    args, kwargs, gas_limit, task_id)


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
        status = blockchain_processor.check_transaction_response(transaction_id)

        if status == 'PENDING':
            self.request.retries = 0
            raise Exception("Need Retry")

    except Exception as e:
        print(e)
        self.retry(countdown=transaction_response_countdown())


@celery_app.task(base=SqlAlchemyTask)
def _log_error(request, exc, traceback, transaction_id):
    blockchain_processor.log_error(request, exc, traceback, transaction_id)
