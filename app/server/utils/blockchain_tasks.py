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
        response = async_result.get(timeout=20, propagate=True, interval=0.3)
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
    Makes a "Transfer From" transaction on an ERC20 token.

    :param signing_address: address of wallet signing txn
    :param token: ERC20 token being transferred
    :param from_address: address of wallet sending token
    :param to_address:
    :param amount: the NON WEI amount being sent, eg 2.3 Dai
    :param dependent_on_tasks: list of task IDs that must complete before txn will attempt
    :return: task id for the transfer
    """

    transfer_sig = celery_app.signature(
        eth_endpoint('transact_with_contract_function'),
        kwargs={
            'signing_address': signing_address,
            'contract_address': token.address,
            'abi_type': 'ERC20',
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
                  safe_set=False,
                  dependent_on_tasks=None):

    zero_set_id_list = None
    if safe_set:
        zero_set_sig = celery_app.signature(
            eth_endpoint('transact_with_contract_function'),
            kwargs={
                'signing_address': signing_address,
                'contract_address': token.address,
                'abi_type': 'ERC20',
                'function': 'approve',
                'args': [
                    spender,
                    0
                ],
                'dependent_on_tasks': dependent_on_tasks
            })

        zero_set_id_list = [execute_synchronous_transaction_task(zero_set_sig)]

    transfer_sig = celery_app.signature(
        eth_endpoint('transact_with_contract_function'),
        kwargs={
            'signing_address': signing_address,
            'contract_address': token.address,
            'abi_type': 'ERC20',
            'function': 'approve',
            'args': [
                spender,
                token.system_amount_to_token(amount)
            ],
            'dependent_on_tasks': zero_set_id_list or dependent_on_tasks
        })

    return execute_synchronous_transaction_task(transfer_sig)


def make_liquid_token_exchange(signing_address,
                               exchange_contract_address,
                               from_token,
                               to_token,
                               reserve_token,
                               from_amount,
                               dependent_on_tasks=None):
    """
    Uses a Liquid Token Contract network to exchange between two ERC20 smart tokens.
    :param signing_address: address of wallet signing txn
    :param exchange_contract_address: the address of the one of the convert contracts used in the network
    :param from_token: the token being exchanged from
    :param to_token: the token being exchanged to
    :param reserve_token: the reserve token used as a connector in the network
    :param from_amount: the amount of the token being exchanged from
    :param dependent_on_tasks: list of task IDs that must complete before txn will attempt
    :return: task id for the exchange
    """

    path = _get_path(from_token, to_token, reserve_token)

    transfer_sig = celery_app.signature(
        eth_endpoint('transact_with_contract_function'),
        kwargs={
            'signing_address': signing_address,
            'contract_address': exchange_contract_address,
            'abi_type': 'bancor_converter',
            'function': 'quickConvert',
            'args': [
                path,
                from_token.system_amount_to_token(from_amount),
                1
            ],
            'dependent_on_tasks': dependent_on_tasks
        })

    return execute_synchronous_transaction_task(transfer_sig)


def get_conversion_amount(exchange_contract_address, from_token, to_token, reserve_token, from_amount):
    """
    Estimates the conversion amount received from a Liquid Token Contract network
    :param exchange_contract_address: the address of the one of the convert contracts used in the network
    :param from_token: the token being exchanged from
    :param to_token: the token being exchanged to
    :param reserve_token: the reserve token used as a connector in the network
    :param from_amount: the amount of the token being exchanged from
    """

    path = _get_path(from_token, to_token, reserve_token)

    conversion_amount_sig = celery_app.signature(
        eth_endpoint('call_contract_function'),
        kwargs={
            'contract_address': exchange_contract_address,
            'abi_type': 'bancor_converter',
            'function': 'quickConvert',
            'args': [
                path,
                from_token.system_amount_to_token(from_amount),
                1
            ],
        })

    raw_conversion_amount = execute_synchronous_call_task(conversion_amount_sig)

    return to_token.token_amount_to_system(raw_conversion_amount)


def _get_path(from_token, to_token, reserve_token):

    if from_token == reserve_token:
        return[
            reserve_token.address,
            to_token.address,
            to_token.address
        ]

    elif to_token == reserve_token:
        return [
            from_token.address,
            from_token.address,
            reserve_token.address,
        ]

    else:
        return [
            from_token.address,
            from_token.address,
            reserve_token.address,
            to_token.address,
            to_token.address
        ]


def get_token_decimals(token):

    decimals_sig = celery_app.signature(eth_endpoint('call_contract_function'),
                                         kwargs={
                                             'contract_address': token.address,
                                             'abi_type': 'ERC20',
                                             'function': 'decimals'
                                         })

    if current_app.config['IS_TEST']:
        # TODO: We need a better way of stubbing responses from the blockchain worker during tests
        return 18

    return execute_synchronous_call_task(decimals_sig)


def get_wallet_balance(address, token):

    balance_sig = celery_app.signature(
        eth_endpoint('call_contract_function'),
        kwargs={
            'contract_address': token.address,
            'abi_type': 'ERC20',
            'function': 'balanceOf',
            'args': [address]
        })

    balance = execute_synchronous_call_task(balance_sig)

    if current_app.config['IS_TEST']:
        # TODO: We need a better way of stubbing responses from the blockchain worker during tests
        return 100000000000000

    return token.token_amount_to_system(balance)

def get_blockchain_task(task_id):
    """
    Used to check the status of a blockchain task

    :param task_id: id of the blockchain
    :return: Serialised Task Dictionary:
    {
        status: enum, one of 'SUCCESS', 'PENDING', 'UNSTARTED', 'FAILED', 'UNKNOWN'
        dependents: list of dependent task ids
    }
    """

    sig = celery_app.signature(eth_endpoint('get_task'),
                               kwargs={'task_id': task_id})

    return execute_synchronous_call_task(sig)
