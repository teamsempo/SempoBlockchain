from celery import signature
from functools import partial
from toolz import pipe

import config
from eth_manager import persistence_interface, utils, w3
from eth_manager.task_interfaces.regular import (
    deploy_contract_task,
    transaction_task,
    send_eth_task,
    synchronous_call,
    await_task_success,
    get_wallet_balance
)

timeout = config.SYNCRONOUS_TASK_TIMEOUT

def get_contract_address(task_uuid):
    await_tr = partial(await_task_success, timeout=timeout)
    return pipe(task_uuid, await_tr, lambda r: r.get('contract_address'))


def topup_wallets():
    wallets = persistence_interface.get_all_wallets()

    for wallet in wallets:
        if (wallet.wei_topup_threshold or 0) > 0:

            last_topup_task_uuid = wallet.last_topup_task_uuid

            if last_topup_task_uuid:
                task = persistence_interface.get_task_from_uuid(last_topup_task_uuid)

                if task.status in ['PENDING', 'UNSTARTED']:
                    return

            signature(utils.eth_endpoint('topup_wallet_if_required'),
                      kwargs={
                          'address': wallet.address
                      }).delay()


def topup_if_required(address):
    balance = w3.eth.getBalance(address)

    wallet = persistence_interface.get_wallet_by_address(address)
    wei_topup_threshold = wallet.wei_topup_threshold
    wei_target_balance = wallet.wei_target_balance or 0

    if balance <= wei_topup_threshold and wei_target_balance > balance:
        sig = signature(utils.eth_endpoint('send_eth'),
                        kwargs={
                            'signing_address': config.MASTER_WALLET_ADDRESS,
                            'amount_wei': wei_target_balance - balance,
                            'recipient_address': address,
                            'prior_tasks': []
                        })

        task_uuid = utils.execute_task(sig)

        persistence_interface.set_wallet_last_topup_task_uuid(address, task_uuid)

        return task_uuid

    return None


def deploy_exchange_network(deploying_address):
    gasPrice = int(2.5e11)

    def deployer(contract_name, args=None):
        return deploy_contract_task(deploying_address, contract_name, args)

    def register_contract(task_uuid, name):

        contract_to_be_registered_id = synchronous_call(
            contract_address=id_contract_address,
            contract_type='ContractIds',
            func=name
        )

        task = await_task_success(task_uuid, timeout=timeout)
        contract_address = task['contract_address']

        return transaction_task(
            signing_address=deploying_address,
            contract_address=registry_contract_address,
            contract_type='ContractRegistry',
            func='registerAddress',
            args=[
                {'type': 'bytes', 'data': contract_to_be_registered_id},
                contract_address
            ],
            gas_limit=8000000
        )

    reg_deploy = deployer(contract_name='ContractRegistry')
    ids_deploy = deployer(contract_name='ContractIds')

    registry_contract_address = get_contract_address(reg_deploy)
    id_contract_address = get_contract_address(ids_deploy)

    features_deploy = deployer(contract_name='ContractFeatures')

    price_limit_deploy = deployer(contract_name='BancorGasPriceLimit',
                                  args=[gasPrice])

    formula_deploy = deployer(contract_name='BancorFormula')

    nst_reg_deploy = deployer(contract_name='NonStandardTokenRegistry')

    network_deploy = deployer(contract_name='BancorNetwork',
                              args=[registry_contract_address])

    # factory_deploy = deployer(contract_name='BancorConverterFactory')

    factory_upgrader_deploy = deployer(contract_name='BancorConverterUpgrader',
                                       args=[registry_contract_address])

    register_contract(features_deploy, 'CONTRACT_FEATURES')
    register_contract(price_limit_deploy, 'BANCOR_GAS_PRICE_LIMIT')
    register_contract(formula_deploy, 'BANCOR_FORMULA')
    register_contract(nst_reg_deploy, 'NON_STANDARD_TOKEN_REGISTRY')
    register_contract(network_deploy, 'BANCOR_NETWORK')
    # register_contract(factory_deploy, 'BANCOR_CONVERTER_FACTORY')
    register_contract(factory_upgrader_deploy, 'BANCOR_CONVERTER_UPGRADER')

    network_address = get_contract_address(network_deploy)

    set_signer_task = transaction_task(
        signing_address=deploying_address,
        contract_address=network_address,
        contract_type='BancorNetwork',
        func='setSignerAddress',
        args=[deploying_address],
        gas_limit=8000000
    )

    res = await_task_success(set_signer_task, timeout=timeout)

    return registry_contract_address


def deploy_and_fund_reserve_token(deploying_address, name, symbol, fund_amount_wei):

    deploy_task_uuid = deploy_contract_task(
        deploying_address,
        'WrappedDai',
        [name, symbol]
    )

    reserve_token_address = get_contract_address(deploy_task_uuid)

    send_eth_task_id = send_eth_task(deploying_address, fund_amount_wei, reserve_token_address)

    res = await_task_success(send_eth_task_id, timeout=timeout)

    balance = synchronous_call(
        contract_address=reserve_token_address,
        contract_type='WrappedDai',
        func='balanceOf',
        args=[deploying_address]
    )

    print(f'Account balance for {reserve_token_address} is: {balance}')

    return reserve_token_address


def deploy_smart_token(
        deploying_address,
        name, symbol, decimals,
        reserve_deposit_wei,
        issue_amount_wei,
        contract_registry_address,
        reserve_token_address,
        reserve_ratio_ppm):

    def with_log(message, uuid):
        print(f'{message}: {uuid}')
        return uuid

    deploy_smart_token_task_uuid = with_log(
        'Deploying smart token',
        deploy_contract_task(
            deploying_address,
            'SmartToken',
            [name, symbol, decimals]
        ))

    smart_token_address = get_contract_address(deploy_smart_token_task_uuid)

    with_log(
        'Issuing smart token bal',
        transaction_task(
            signing_address=deploying_address,
            contract_address=smart_token_address,
            contract_type='SmartToken',
            func='issue',
            args=[deploying_address, issue_amount_wei],
            gas_limit=8000000
        ))

    deploy_subexchange_task_uuid = with_log(
        'Deploying converter',
        deploy_contract_task(
            deploying_address,
            'BancorConverter',
            [smart_token_address, contract_registry_address, 30000, reserve_token_address, reserve_ratio_ppm]
        ))

    subexchange_address = get_contract_address(deploy_subexchange_task_uuid)

    bal = get_wallet_balance(
        address=deploying_address,
        token_address=reserve_token_address
    )

    print(f'Wallet balance for {reserve_token_address} is \n'
          f'{bal} wei. Depositing \n'
          f'{reserve_deposit_wei} wei).')

    with_log(
        'Transfering reserve deposit',
        transaction_task(
            signing_address=deploying_address,
            contract_address=reserve_token_address,
            contract_type='EtherToken',
            func='transfer',
            args=[subexchange_address, reserve_deposit_wei],
            gas_limit=100000
        ))

    with_log(
        'Approving converter for ethertoken',
        transaction_task(
            signing_address=deploying_address,
            contract_address=reserve_token_address,
            contract_type='EtherToken',
            func='approve',
            args=[subexchange_address, '1000000000000000000000000000000000000'],
            gas_limit=100000
        ))

    with_log(
        'Approving converter for smart token',
        transaction_task(
            signing_address=deploying_address,
            contract_address=smart_token_address,
            contract_type='SmartToken',
            func='approve',
            args=[subexchange_address, '1000000000000000000000000000000000000'],
            gas_limit=100000
        )
    )

    transfer_ownership_id = with_log(
        'Transfering ownership of smart token',
        transaction_task(
            signing_address=deploying_address,
            contract_address=smart_token_address,
            contract_type='SmartToken',
            func='transferOwnership',
            args=[subexchange_address],
            gas_limit=100000
        ))

    with_log(
        'Accepting Ownership',
        transaction_task(
            signing_address=deploying_address,
            contract_address=subexchange_address,
            contract_type='BancorConverter',
            func='acceptTokenOwnership',
            gas_limit=100000,
            prior_tasks=[transfer_ownership_id]
        ))

    return {'smart_token_address': smart_token_address,
            'subexchange_address': subexchange_address}

