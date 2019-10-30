from typing import Optional, List, Dict
from functools import partial
from flask import current_app
from eth_keys import keys
from eth_utils import keccak
import os
import random

from server import celery_app
from server.utils.exchange import (
    bonding_curve_tokens_to_reserve,
    bonding_curve_reserve_to_tokens,
    bonding_curve_token1_to_token2
)


def eth_endpoint(endpoint):
    eth_worker_name = 'eth_manager'
    celery_tasks_name = 'celery_tasks'
    return f'{eth_worker_name}.{celery_tasks_name}.{endpoint}'


def execute_synchronous_celery(signature, timeout=None):
    async_result = signature.delay()

    try:
        response = async_result.get(timeout=timeout or 20, propagate=True, interval=0.3)
    except Exception as e:
        raise e
    finally:
        async_result.forget()

    return response


def execute_synchronous_task(signature):
    if current_app.config['IS_TEST']:
        # TODO: We need a better way of stubbing responses from the blockchain worker during tests
        return random.randint(0, 1000000000)

    return execute_synchronous_celery(signature)


def synchronous_call(contract_address, contract_type, func, args=None, signing_address=None):
    call_sig = celery_app.signature(
        eth_endpoint('call_contract_function'),
        kwargs={
            'contract_address': contract_address,
            'abi_type': contract_type,
            'function': func,
            'args': args,
            'signing_address': signing_address
        })

    return execute_synchronous_celery(call_sig)


def synchronous_transaction_task(signing_address,
                                 contract_address, contract_type,
                                 func, args=None,
                                 gas_limit=None,
                                 dependent_on_tasks=None):

    signature = celery_app.signature(
        eth_endpoint('transact_with_contract_function'),
        kwargs={
            'signing_address': signing_address,
            'contract_address': contract_address,
            'abi_type': contract_type,
            'function': func,
            'args': args,
            'gas_limit': gas_limit,
            'dependent_on_tasks': dependent_on_tasks
        })

    return execute_synchronous_task(signature)


def create_blockchain_wallet(wei_target_balance=0, wei_topup_threshold=0):

    if not current_app.config['IS_TEST']:
        sig = celery_app.signature(eth_endpoint('create_new_blockchain_wallet'),
                                   kwargs={
                                       'wei_target_balance': wei_target_balance,
                                       'wei_topup_threshold': wei_topup_threshold,
                                   })

        return execute_synchronous_celery(sig)
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

    return execute_synchronous_task(transfer_sig)


def deploy_contract(
        signing_address: str,
        contract_name: str,
        constructor_args: Optional[List] = None,
        constructor_kwargs: Optional[Dict] = None,
        dependent_on_tasks: Optional[List[int]] = None) -> int:

    deploy_sig = celery_app.signature(
        eth_endpoint('deploy_contract'),
        kwargs={
            'signing_address': signing_address,
            'contract_name': contract_name,
            'args': constructor_args,
            'kwargs': constructor_kwargs,
            'dependent_on_tasks': dependent_on_tasks
        })

    return execute_synchronous_task(deploy_sig)


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

    return synchronous_transaction_task(
        signing_address=signing_address,
        contract_address=token.address,
        contract_type='ERC20',
        func='transferFrom',
        args=[
            from_address,
            to_address,
            token.system_amount_to_token(amount)
        ],
        dependent_on_tasks=dependent_on_tasks
    )


def make_approval(signing_address, token,
                  spender, amount,
                  dependent_on_tasks=None):

    return synchronous_transaction_task(
        signing_address=signing_address,
        contract_address=token.address,
        contract_type='ERC20',
        func='approve',
        args=[
            spender,
            token.system_amount_to_token(amount)
        ],
        dependent_on_tasks=dependent_on_tasks
    )


def make_liquid_token_exchange(signing_address,
                               exchange_contract,
                               from_token,
                               to_token,
                               reserve_token,
                               from_amount,
                               dependent_on_tasks=None):
    """
    Uses a Liquid Token Contract network to exchange between two ERC20 smart tokens.
    :param signing_address: address of wallet signing txn
    :param exchange_contract: the base convert contract used in the network
    :param from_token: the token being exchanged from
    :param to_token: the token being exchanged to
    :param reserve_token: the reserve token used as a connector in the network
    :param from_amount: the amount of the token being exchanged from
    :param dependent_on_tasks: list of task IDs that must complete before txn will attempt
    :return: task id for the exchange
    """

    path = _get_path(from_token, to_token, reserve_token)

    return synchronous_transaction_task(
        signing_address=signing_address,
        contract_address=exchange_contract.address,
        contract_type='bancor_converter',
        func='quickConvert',
        args=[
            path,
            from_token.system_amount_to_token(from_amount),
            1
        ],
        dependent_on_tasks=dependent_on_tasks
    )


def get_conversion_amount(exchange_contract, from_token, to_token, from_amount, signing_address=None):
    """
    Estimates the conversion amount received from a Liquid Token Contract network
    :param exchange_contract: the base convert contract used in the network
    :param from_token: the token being exchanged from
    :param to_token: the token being exchanged to
    :param from_amount: the amount of the token being exchanged from
    """

    def get_token_exchange_details(token):
        subexchange_details = exchange_contract.get_subexchange_details(token.address)
        subexchange_address = subexchange_details['subexchange_address']

        token_supply = synchronous_call(
            contract_address=token.address,
            contract_type='ERC20Token',
            func='totalSupply'
        )

        subexchange_reserve = synchronous_call(
            contract_address=reserve_token.address,
            contract_type='ERC20Token',
            func='balanceOf',
            args=[subexchange_address]
        )

        subexchange_reserve_ratio_ppm = subexchange_details['subexchange_reserve_ratio_ppm']

        return token_supply, subexchange_reserve, subexchange_reserve_ratio_ppm

    raw_from_amount = from_token.system_amount_to_token(from_amount)

    reserve_token = exchange_contract.reserve_token

    from_is_reserve = from_token == reserve_token
    to_is_reserve = to_token == reserve_token

    if (not from_is_reserve) and (not to_is_reserve):

        (from_token_supply,
         from_subexchange_reserve,
         from_subexchange_reserve_ratio_ppm) = get_token_exchange_details(from_token)

        (to_token_supply,
         to_subexchange_reserve,
         to_subexchange_reserve_ratio_ppm) = get_token_exchange_details(to_token)

        to_amount = bonding_curve_token1_to_token2(from_token_supply, to_token_supply,
                                                   from_subexchange_reserve, to_subexchange_reserve,
                                                   from_subexchange_reserve_ratio_ppm, to_subexchange_reserve_ratio_ppm,
                                                   raw_from_amount)

    elif not from_is_reserve:
        (from_token_supply,
         from_subexchange_reserve,
         from_subexchange_reserve_ratio_ppm) = get_token_exchange_details(from_token)

        to_amount = bonding_curve_tokens_to_reserve(from_token_supply,
                                                    from_subexchange_reserve,
                                                    from_subexchange_reserve_ratio_ppm,
                                                    raw_from_amount)

    else:
        (to_token_supply,
         to_subexchange_reserve,
         to_subexchange_reserve_ratio_ppm) = get_token_exchange_details(to_token)

        to_amount = bonding_curve_reserve_to_tokens(to_token_supply,
                                                    to_subexchange_reserve,
                                                    to_subexchange_reserve_ratio_ppm,
                                                    raw_from_amount)

    to_amount = round(to_amount)

    # path = _get_path(from_token, to_token, reserve_token)
    #
    # to_amount = synchronous_call(
    #     contract_address=exchange_contract.blockchain_address,
    #     contract_type='bancor_converter',
    #     func='quickConvert',
    #     args=[
    #         path,
    #         from_token.system_amount_to_token(from_amount),
    #         1
    #     ],
    #     signing_address=signing_address)

    return to_token.token_amount_to_system(to_amount)


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

    if current_app.config['IS_TEST']:
        # TODO: We need a better way of stubbing responses from the blockchain worker during tests
        return 18

    return synchronous_call(
        contract_address=token.address,
        contract_type='ERC20',
        func='decimals'
    )

def get_wallet_balance(address, token):

    if current_app.config['IS_TEST']:
        # TODO: We need a better way of stubbing responses from the blockchain worker during tests
        return 100000000000000

    balance = synchronous_call(
        contract_address=token.address,
        contract_type='ERC20',
        func='balanceOf',
        args=[address])

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

    return execute_synchronous_celery(sig)


def deploy_reserve_network(deploying_address):

    sig = celery_app.signature(eth_endpoint('deploy_reserve_network'),
                               args=[deploying_address])

    return execute_synchronous_celery(sig, timeout=900)


def deploy_and_fund_reserve_token(deploying_address, fund_amount_wei):
    sig = celery_app.signature(eth_endpoint('deploy_and_fund_reserve_token'),
                               args=[deploying_address, fund_amount_wei])

    return execute_synchronous_celery(sig, timeout=900)


def deploy_smart_token(deploying_address,
                       name, symbol, decimals,
                       issue_amount_wei,
                       contract_registry_address,
                       reserve_token_address,
                       reserve_ratio_ppm):

    sig = celery_app.signature(eth_endpoint('deploy_smart_token'),
                               args=[deploying_address,
                                     name, symbol, decimals,
                                     int(issue_amount_wei),
                                     contract_registry_address,
                                     reserve_token_address,
                                     int(reserve_ratio_ppm)])

    return execute_synchronous_celery(sig, timeout=900)

    # gasPrice = 100000
    #
    # deployer = partial(deploy_contract, signing_address)
    #
    # reg_deploy = deployer(contract_name='ContractRegistry')
    # ids_deploy = deployer(contract_name='ContractIds')
    # features_deploy = deployer(contract_name='ContractFeatures')
    # price_limit_deploy = deployer(contract_name='BancorGasPriceLimit',
    #                               constructor_args=[gasPrice])
    # formula_deploy = deployer(contract_name='BancorFormula')
    # nst_reg_deploy = deployer(contract_name='NonStandardTokenRegistry')
    # # network_deploy = deployer(contract_name='BancorNetwork')