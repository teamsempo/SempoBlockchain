from time import sleep

from celery import signature

from eth_manager import utils


def deploy_contract_task(signing_address, contract_name, args=None):
    deploy_sig = signature(
        utils.eth_endpoint('deploy_contract'),
        kwargs={
            'signing_address': signing_address,
            'contract_name': contract_name,
            'args': args
        })

    return utils.execute_synchronous_task(deploy_sig)


def transaction_task(signing_address,
                     contract_address, contract_type,
                     func, args=None,
                     gas_limit=None,
                     dependent_on_tasks=None):

    kwargs = {
        'signing_address': signing_address,
        'contract_address': contract_address,
        'abi_type': contract_type,
        'function': func,
        'args': args,
        'dependent_on_tasks': dependent_on_tasks
    }

    if gas_limit:
        kwargs['gas_limit'] = gas_limit

    sig = signature(
        utils.eth_endpoint('transact_with_contract_function'),
        kwargs=kwargs)

    return utils.execute_synchronous_task(sig)


def send_eth_task(signing_address, amount_wei, recipient_address):
    sig = signature(
        utils.eth_endpoint('send_eth'),
        kwargs={
            'signing_address': signing_address,
            'amount_wei': amount_wei,
            'recipient_address': recipient_address
        })

    return utils.execute_synchronous_task(sig)


def synchronous_call(contract_address, contract_type, func, args=None):
    call_sig = signature(
        utils.eth_endpoint('call_contract_function'),
        kwargs={
            'contract_address': contract_address,
            'abi_type': contract_type,
            'function': func,
            'args': args,
        })

    return utils.execute_synchronous_task(call_sig)


def await_task_success(task_id, timeout=None, poll_frequency=0.5):
    elapsed = 0
    while timeout is None or elapsed <= timeout:
        task_sig = signature(
            utils.eth_endpoint('get_task'),
            kwargs={'task_id': task_id}
        )

        task = utils.execute_synchronous_task(task_sig)

        if task['status'] == 'SUCCESS':
            return task
        else:
            sleep(poll_frequency)
            elapsed += poll_frequency

    raise TimeoutError
