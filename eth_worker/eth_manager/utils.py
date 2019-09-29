import requests
from requests.auth import HTTPBasicAuth

from eth_manager.ABIs import dai_abi
import eth_manager

eth_worker_name = 'eth_manager'
celery_tasks_name = 'celery_tasks'
eth_endpoint = lambda endpoint: f'{eth_worker_name}.{celery_tasks_name}.{endpoint}'

def register_contracts_from_app(host_address, auth_username, auth_password):

    token_req = requests.get(host_address + '/api/token', auth=HTTPBasicAuth(auth_username, auth_password))

    for token in token_req.json()['data']['tokens']:
        eth_manager.blockchain_processor.registry.register_contract(token['address'], dai_abi.abi)

def execute_synchronous_task(signature):
    async_result = signature.delay()

    try:
        response = async_result.get(timeout=2, propagate=True, interval=0.3)
    except Exception as e:
        raise e
    finally:
        async_result.forget()

    return response
