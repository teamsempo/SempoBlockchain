from time import sleep

from celery import signature

from celery_dispatchers import utils

def deploy_contract_task(signing_address, contract_name, args=None, prior_tasks=None):
    deploy_sig = signature(
        utils.eth_endpoint('deploy_contract'),
        kwargs={
            'signing_address': signing_address,
            'contract_name': contract_name,
            'args': args,
            'prior_tasks': prior_tasks
        })

    return utils.queue_sig(deploy_sig)


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

    return utils.queue_sig(sig)


def send_eth_task(signing_address, amount_wei, recipient_address):
    sig = signature(
        utils.eth_endpoint('send_eth'),
        kwargs={
            'signing_address': signing_address,
            'amount_wei': amount_wei,
            'recipient_address': recipient_address
        })

    return utils.queue_sig(sig)


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


def queue_attempt_transaction(task_uuid, countdown=0):
    sig = signature(
        utils.eth_endpoint('_attempt_transaction'),
        kwargs={'task_uuid': task_uuid}
    )

    return utils.queue_sig(sig, countdown=countdown)


def queue_send_eth(
        signing_address,
        amount_wei,
        recipient_address,
        prior_tasks,
        posterior_tasks,
):
    sig = signature(utils.eth_endpoint('send_eth'),
                    kwargs={
                        'signing_address': signing_address,
                        'amount_wei': amount_wei,
                        'recipient_address': recipient_address,
                        'prior_tasks': prior_tasks,
                        'posterior_tasks': posterior_tasks
                    })

    return utils.queue_sig(sig)


def sig_process_send_eth_transaction(
        transaction_id,
        recipient_address,
        transfer_amount,
        task_id
):
    return signature(
        utils.eth_endpoint('_process_send_eth_transaction'),
        args=(
            transaction_id,
            recipient_address,
            transfer_amount,
            task_id
        )
    )


def sig_process_function_transaction(
    transaction_id,
    contract_address,
    abi_type,
    fn,
    args,
    kwargs,
    gas_limit,
    task_id
):
    return signature(
        utils.eth_endpoint('_process_function_transaction'),
        args=(
            transaction_id,
            contract_address,
            abi_type,
            fn,
            args,
            kwargs,
            gas_limit,
            task_id
        )
    )


def sig_process_deploy_contract_transaction(
    transaction_id,
    contract_name,
    args,
    kwargs,
    gas_limit,
    task_id
):
    signature(
        utils.eth_endpoint('_process_deploy_contract_transaction'),
        args=(
            transaction_id,
            contract_name,
            args,
            kwargs,
            gas_limit,
            task_id
        )
    )


def sig_check_transaction_response():
    return signature(utils.eth_endpoint('_check_transaction_response'))


def sig_log_error(transaction_id):
    return signature(utils.eth_endpoint('_log_error'), args=(transaction_id,))
