
worker_function_returns = {
    'deploy_exchange_network': deploy_exchange_network
}


def simulate(sig):
    id = 123 # make this random
    if sig in worker_function_returns:
        return (id, worker_function_returns[sig](sig)) # Make this a named touple
    else:
        return (id, None)


# Reference blockchain_tasker.py

# Worker: eth_worker
# Input: deploying_address
# Side effects: 
# Return value: registry_contract_address
def deploy_exchange_network(sig):
    return 'pass'

# Worker: eth_worker
# Input: signing_address, recipient_address, amount_wei
# Side effects: 
# Return value: task_id
def send_eth(sig):
    pass
