from . import blockchain_tasks_simulator

endpoint_simulators = {
    'eth_manager.celery_tasks.deploy_contract': blockchain_tasks_simulator.deploy_contract,
    'eth_manager.celery_tasks.call_contract_function': blockchain_tasks_simulator.call_contract_function,
    'eth_manager.celery_tasks.transact_with_contract_function': blockchain_tasks_simulator.transact_with_contract_function,
    'eth_manager.celery_tasks.get_task': blockchain_tasks_simulator.get_task,
    'eth_manager.celery_tasks.retry_task': blockchain_tasks_simulator.retry_task,
    'eth_manager.celery_tasks.retry_failed': blockchain_tasks_simulator.retry_failed,
    'eth_manager.celery_tasks.create_new_blockchain_wallet': blockchain_tasks_simulator.create_new_blockchain_wallet,
    'eth_manager.celery_tasks.deploy_exchange_network': blockchain_tasks_simulator.deploy_exchange_network,
    'eth_manager.celery_tasks.deploy_and_fund_reserve_token': blockchain_tasks_simulator.deploy_and_fund_reserve_token,
    'eth_manager.celery_tasks.deploy_smart_token': blockchain_tasks_simulator.deploy_smart_token,
    'eth_manager.celery_tasks.topup_wallet_if_required': blockchain_tasks_simulator.topup_wallet_if_required,
    'eth_manager.celery_tasks.send_eth': blockchain_tasks_simulator.send_eth,
}

def simulate(task, kwargs, args):
    print('[WARN] Worker Simulator is running. This task will NOT be executed on the blockchain. Never use this mode in prod, or else bad stuff will happen')
    print((task, kwargs, args))
    if task in endpoint_simulators:
        return endpoint_simulators[task](kwargs, args)
    else:
        print('[WARN] Task \'${task}\' does not have a simulator. Please add one to worker_simulator.endpoint_simulators. Using generic response.')
        return blockchain_tasks_simulator.FakeCeleryAsyncResult()
