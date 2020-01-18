
worker_function_returns = {
    'deploy_exchange_network': deploy_exchange_network
}

def simulate(sig):
    id = 123 # make this random
    if sig in worker_function_returns:
        return (id, worker_function_returns[sig](sig)) # Make this a named touple
    else:

def deploy_exchange_network(sig):
    return 'pass'