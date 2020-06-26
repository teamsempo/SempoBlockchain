import celery
import traceback

from celery import signals

import config
from celery_app import app, processor, supervisor, task_manager, persistence_module
from exceptions import (
    LockedNotAcquired
)

import composite_tasks as composite


class SqlAlchemyTask(celery.Task):
    """An abstract Celery Task that ensures that the connection the the
    database is closed on task completion"""
    abstract = True

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        try:
            persistence_module.session.remove()
        except:
            pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        try:
            persistence_module.session.remove()
        except:
            pass

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        try:
            persistence_module.session.remove()
            persistence_module.session = scoped_session(session)
        except:
            pass

    def on_success(self, retval, task_id, args, kwargs):
        try:
            persistence_module.session.remove()
        except:
            pass

base_task_config = {
    'base': SqlAlchemyTask,
    'bind': True,
    'autoretry_for': (Exception,),
    'max_retries': 3,
    'soft_time_limit': 300,
    'retry_backoff': True
}

low_priority_config = {
    **base_task_config,
    'queue': 'low-priority'
}

no_retry_config = {
    **base_task_config,
    'max_retries': 0
}

processor_task_config = {
    **base_task_config,
    'max_retries': 10,
    'autoretry_for': (LockedNotAcquired,),
    'queue': 'processor',
    'default_retry_delay': 3,
    'retry_backoff': False
}

# @signals.task_failure.connect
# def on_task_failure(**kwargs):
#     print('[task:%s]' % (kwargs['sender'].request.correlation_id, )
#           + '\n'
#           + kwargs.get('einfo').traceback)

@app.task(**base_task_config)
def deploy_exchange_network(self, deploying_address):
    return composite.deploy_exchange_network(deploying_address)


@app.task(**base_task_config)
def deploy_and_fund_reserve_token(self, deploying_address, name, symbol, fund_amount_wei):
    return composite.deploy_and_fund_reserve_token(
        deploying_address,
        name, symbol, fund_amount_wei)


@app.task(**base_task_config)
def deploy_smart_token(self, deploying_address,
                       name, symbol, decimals,
                       reserve_deposit_wei,
                       issue_amount_wei,
                       contract_registry_address,
                       reserve_token_address,
                       reserve_ratio_ppm):

    return composite.deploy_smart_token(
        deploying_address,
        name, symbol, decimals,
        reserve_deposit_wei,
        issue_amount_wei,
        contract_registry_address,
        reserve_token_address,
        reserve_ratio_ppm)


@app.task(**base_task_config)
def create_new_blockchain_wallet(self, wei_target_balance=0, wei_topup_threshold=0, private_key=None):
    wallet = persistence_module.create_new_blockchain_wallet(wei_target_balance=wei_target_balance,
                                                             wei_topup_threshold=wei_topup_threshold,
                                                             private_key=private_key)
    return wallet.address


@app.task(**low_priority_config)
def topup_wallets(self):
    return composite.topup_wallets()

# Set retry attempts to zero since beat will retry shortly anyway
@app.task(**no_retry_config)
def topup_wallet_if_required(self, address):
    return composite.topup_if_required(address)


@app.task(**base_task_config)
def register_contract(self, contract_address, abi, contract_name=None, require_name_matches=False):
    return processor.registry.register_contract(
        contract_address, abi, contract_name, require_name_matches
    )


@app.task(**base_task_config)
def call_contract_function(self, contract_address, function, abi_type=None, args=None, kwargs=None,
                           signing_address=None):
    return processor.call_contract_function(contract_address, abi_type, function, args, kwargs,
                                            signing_address)


@app.task(**base_task_config)
def transact_with_contract_function(self, contract_address, function,  abi_type=None, args=None, kwargs=None,
                                    signing_address=None, encrypted_private_key=None,
                                    gas_limit=None, prior_tasks=None, reverses_task=None):

    return task_manager.transact_with_contract_function(self.request.id,
                                                                contract_address, abi_type, function, args, kwargs,
                                                                signing_address, encrypted_private_key,
                                                                gas_limit, prior_tasks, reverses_task)


@app.task(**base_task_config)
def deploy_contract(self, contract_name, args=None, kwargs=None,
                    signing_address=None, encrypted_private_key=None,
                    gas_limit=None, prior_tasks=None):

    return task_manager.deploy_contract(self.request.id,
                                                contract_name, args, kwargs,
                                                signing_address, encrypted_private_key,
                                                gas_limit, prior_tasks)


@app.task(**base_task_config)
def send_eth(self, amount_wei, recipient_address,
             signing_address=None, encrypted_private_key=None,
             prior_tasks=None, posterior_tasks=None):

    return task_manager.send_eth(self.request.id,
                                         amount_wei, recipient_address,
                                         signing_address, encrypted_private_key,
                                         prior_tasks, posterior_tasks)


@app.task(**no_retry_config)
def retry_task(self, task_uuid):
    return supervisor.retry_task(task_uuid)


@app.task(**no_retry_config)
def retry_failed(self, min_task_id=None, max_task_id=None, retry_unstarted=False):
    return supervisor.retry_failed(min_task_id, max_task_id, retry_unstarted)


@app.task(**base_task_config)
def get_task(self, task_uuid):
    return supervisor.get_serialised_task_from_uuid(task_uuid)


@app.task(base=SqlAlchemyTask)
def _handle_error(request, exc, traceback, transaction_id):
    return supervisor.handle_error(request, exc, traceback, transaction_id)


@app.task(base=SqlAlchemyTask, bind=True, max_retries=config.ETH_CHECK_TRANSACTION_RETRIES, soft_time_limit=300)
def _check_transaction_response(self, transaction_id):
    return supervisor.check_transaction_response(self, transaction_id)


@app.task(**base_task_config)
def _attempt_transaction(self, task_uuid):
    return supervisor.attempt_transaction(task_uuid)


@app.task(**processor_task_config)
def _process_send_eth_transaction(self, transaction_id, recipient_address, amount, task_id=None):
    return processor.process_send_eth_transaction(transaction_id, recipient_address, amount, task_id)


@app.task(**processor_task_config)
def _process_function_transaction(self, transaction_id, contract_address, abi_type,
                                  function, args=None, kwargs=None,  gas_limit=None, task_id=None):
    return processor.process_function_transaction(transaction_id, contract_address, abi_type,
                                                  function, args, kwargs, gas_limit, task_id)


@app.task(**processor_task_config)
def _process_deploy_contract_transaction(self, transaction_id, contract_name,
                                         args=None, kwargs=None,  gas_limit=None, task_id=None):
    return processor.process_deploy_contract_transaction(transaction_id, contract_name,
                                                         args, kwargs, gas_limit, task_id)