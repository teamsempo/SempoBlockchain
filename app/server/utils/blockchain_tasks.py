from flask import current_app
from server import celery_app
from eth_keys import keys
from eth_utils import keccak
import os, random
eth_worker_name = 'eth_manager'
celery_tasks_name = 'celery_tasks'
eth_endpoint = lambda endpoint: f'{eth_worker_name}.{celery_tasks_name}.{endpoint}'

def _execute_synchronous_celery(signature):
    async_result = signature.delay()

    try:
        response = async_result.get(timeout=2, propagate=True, interval=0.3)
    except Exception as e:
        raise e
    finally:
        async_result.forget()

    return response
    
    
def execute_synchronous_transaction_task(signature):
    if current_app.config['IS_TEST']:
        # TODO: We need a better way of stubbing responses from the blockchain worker during tests
        return random.randint(0, 1000000000)

    return _execute_synchronous_celery(signature)

def execute_synchronous_call_task(signature):
    return _execute_synchronous_celery(signature)


def create_blockchain_wallet(wei_target_balance=0, wei_topup_threshold=0):

    if not current_app.config['IS_TEST']:
        sig = celery_app.signature(eth_endpoint('create_new_blockchain_wallet'),
                                   kwargs={
                                       'wei_target_balance': wei_target_balance,
                                       'wei_topup_threshold': wei_topup_threshold,
                                   })

        return _execute_synchronous_celery(sig)
    else:
        return keys.PrivateKey(os.urandom(32)).public_key.to_checksum_address()

def send_eth(signing_address, recipient_address, amount_wei, dependent_on_tasks=None):

    transfer_sig = celery_app.signature(eth_endpoint('send_eth'),
                                        kwargs={
                                            'signing_address': signing_address,
                                            'amount_wei': amount_wei,
                                            'recipient_address': recipient_address,
                                            'dependent_on_tasks': dependent_on_tasks
                                        })

    return execute_synchronous_transaction_task(transfer_sig)

def make_token_transfer(signing_address, token,
                        from_address, to_address, amount,
                        dependent_on_tasks=None):
    """

    :param signing_address: address of wallet signing txn
    :param token: ERC20 token being transferred
    :param from_address: address of wallet sending token
    :param to_address:
    :param amount: the NON WEI amount being sent, eg 2.3 Dai
    :param dependent_on_tasks: list of task IDs that must complete before txn will attempt
    :return: task id for the transfer
    """

    transfer_sig = celery_app.signature(eth_endpoint('transact_with_contract_function'),
                                kwargs={
                                    'signing_address': signing_address,
                                    'contract': token.address,
                                    'function': 'transferFrom',
                                    'args': [
                                        from_address,
                                        to_address,
                                        token.system_amount_to_token(amount)
                                    ],
                                    'dependent_on_tasks': dependent_on_tasks
                                })

    return execute_synchronous_transaction_task(transfer_sig)



def make_approval(signing_address, token,
                  spender, amount,
                  dependent_on_tasks=None):

    transfer_sig = celery_app.signature(eth_endpoint('transact_with_contract_function'),
                                kwargs={
                                    'signing_address': signing_address,
                                    'contract': token.address,
                                    'function': 'approve',
                                    'args': [
                                        spender,
                                        token.system_amount_to_token(amount)
                                    ],
                                    'gas_limit': 46049,
                                    'dependent_on_tasks': dependent_on_tasks
                                })

    return execute_synchronous_transaction_task(transfer_sig)

def get_token_decimals(token):

    decimals_sig = celery_app.signature(eth_endpoint('call_contract_function'),
                                         kwargs={
                                                      'contract': token.address,
                                                      'function': 'decimals'
                                         })

    if current_app.config['IS_TEST']:
        # TODO: We need a better way of stubbing responses from the blockchain worker during tests
        return 18

    return execute_synchronous_call_task(decimals_sig)

def get_wallet_balance(address, token):

    balance_sig = celery_app.signature(eth_endpoint('call_contract_function'),
                                        kwargs={
                                                     'contract': token.address,
                                                     'function': 'balanceOf',
                                                     'args': [address]
                                        })

    balance = execute_synchronous_call_task(balance_sig)

    if current_app.config['IS_TEST']:
        # TODO: We need a better way of stubbing responses from the blockchain worker during tests
        return 100000000000000

    return token.token_amount_to_system(balance)

def get_blockchain_task(task_id):

    sig = celery_app.signature(eth_endpoint('get_task'),
                               kwargs={'task_id': task_id})

    return execute_synchronous_call_task(sig)