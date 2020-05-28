from time import sleep

from celery import signature

from eth_manager import utils


def deploy_contract_task(signing_address, contract_name, args=None, prior_tasks=None):
    deploy_sig = signature(
        utils.eth_endpoint('deploy_contract'),
        kwargs={
            'signing_address': signing_address,
            'contract_name': contract_name,
            'args': args,
            'prior_tasks': prior_tasks
        })

    return utils.execute_task(deploy_sig)


def transaction_task(signing_address,
                     contract_address, contract_type,
                     func, args=None,
                     gas_limit=None,
                     prior_tasks=None,
                     reverses_task=None):

    kwargs = {
        'signing_address': signing_address,
        'contract_address': contract_address,
        'abi_type': contract_type,
        'function': func,
        'args': args,
        'prior_tasks': prior_tasks,
        'reverses_task': reverses_task
    }

    if gas_limit:
        kwargs['gas_limit'] = gas_limit

    sig = signature(
        utils.eth_endpoint('transact_with_contract_function'),
        kwargs=kwargs)

    return utils.execute_task(sig)


def send_eth_task(signing_address, amount_wei, recipient_address):
    sig = signature(
        utils.eth_endpoint('send_eth'),
        kwargs={
            'signing_address': signing_address,
            'amount_wei': amount_wei,
            'recipient_address': recipient_address
        })

    return utils.execute_task(sig)


def synchronous_call(contract_address, contract_type, func, args=None):
    call_sig = signature(
        utils.eth_endpoint('call_contract_function'),
        kwargs={
            'contract_address': contract_address,
            'abi_type': contract_type,
            'function': func,
            'args': args,
        })

    return utils.execute_synchronous_celery(call_sig)


def get_wallet_balance(address, token_address):

    balance_wei = synchronous_call(
        contract_address=token_address,
        contract_type='ERC20',
        func='balanceOf',
        args=[address])

    return balance_wei


def await_blockchain_success_evil(task_uuid, timeout=None, poll_frequency=0.5):
    elapsed = 0
    print(f'Awaiting success for task uuid: {task_uuid}')
    while timeout is None or elapsed <= timeout:
        sig = signature(
            utils.eth_endpoint('get_task'),
            kwargs={'task_uuid': task_uuid}
        )

        task = utils.execute_synchronous_celery(sig)

        if task and task['status'] == 'SUCCESS':
            return task
        else:
            sleep(poll_frequency)
            elapsed += poll_frequency

    raise TimeoutError


def await_blockchain_success(task_uuid, timeout=None, poll_frequency=0.5):
    elapsed = 0
    print(f'Awaiting success for task uuid: {task_uuid}')
    while timeout is None or elapsed <= timeout:
        sig = signature(
            utils.eth_endpoint('get_task'),
            kwargs={'task_uuid': task_uuid}
        )

        task = utils.execute_synchronous_celery(sig)

        if task and task['status'] == 'SUCCESS':
            return task
        else:
            sleep(poll_frequency)
            elapsed += poll_frequency

    raise TimeoutError


