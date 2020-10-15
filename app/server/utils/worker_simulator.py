from . import blockchain_tasks_simulator

endpoint_simulators = {
    'ETHEREUM.celery_tasks.deploy_contract': blockchain_tasks_simulator.deploy_contract,
    'ETHEREUM.celery_tasks.call_contract_function': blockchain_tasks_simulator.call_contract_function,
    'ETHEREUM.celery_tasks.transact_with_contract_function': blockchain_tasks_simulator.transact_with_contract_function,
    'ETHEREUM.celery_tasks.get_task': blockchain_tasks_simulator.get_task,
    'ETHEREUM.celery_tasks.retry_task': blockchain_tasks_simulator.retry_task,
    'ETHEREUM.celery_tasks.retry_failed': blockchain_tasks_simulator.retry_failed,
    'ETHEREUM.celery_tasks.create_new_blockchain_wallet': blockchain_tasks_simulator.create_new_blockchain_wallet,
    'ETHEREUM.celery_tasks.deploy_exchange_network': blockchain_tasks_simulator.deploy_exchange_network,
    'ETHEREUM.celery_tasks.deploy_and_fund_reserve_token': blockchain_tasks_simulator.deploy_and_fund_reserve_token,
    'ETHEREUM.celery_tasks.deploy_smart_token': blockchain_tasks_simulator.deploy_smart_token,
    'ETHEREUM.celery_tasks.topup_wallet_if_required': blockchain_tasks_simulator.topup_wallet_if_required,
    'ETHEREUM.celery_tasks.send_eth': blockchain_tasks_simulator.send_eth,
}

def simulate(task, kwargs, args, queue):
    print('[WARN] Worker Simulator is running. This task will NOT be executed on the blockchain. Never use this mode in prod, or else bad stuff will happen')
    if task in endpoint_simulators:
        return endpoint_simulators[task](kwargs, args)
    else:
        print('[WARN] Task \'{}\' does not have a simulator. Please add one to worker_simulator.endpoint_simulators. Using generic response.'.format(task))
        return blockchain_tasks_simulator.FakeCeleryAsyncResult()
