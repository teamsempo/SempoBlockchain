from time import sleep

from celery import signature
import os
import config

chain = os.environ.get('CHAIN', config.DEFAULT_CHAIN)

celery_tasks_name = 'celery_tasks'
eth_endpoint = lambda endpoint: f'{chain}.{celery_tasks_name}.{endpoint}'


def execute_synchronous_celery(signature):
    async_result = signature.delay()
    try:
        response = async_result.get(
            timeout=config.CHAINS[chain]['SYNCRONOUS_TASK_TIMEOUT'],
            propagate=True,
            interval=0.3)

    except Exception as e:
        raise e
    finally:
        async_result.forget()

    return response


def queue_sig(sig, countdown=0):
    ar = sig.apply_async(
        countdown=countdown
    )

    return ar.id


def await_blockchain_success(task_uuid, timeout=None, poll_frequency=0.5):
    # TODO: This should definitely be refactored to use celery chains, as it can potentially cause queue blocking
    # The only reason we get away with it now is because await_blockchain_success is only really used for system setup
    # And so is called very rarely
    elapsed = 0
    print(f'Awaiting success for task uuid: {task_uuid}')
    while timeout is None or elapsed <= timeout:
        sig = signature(
            eth_endpoint('get_task'),
            kwargs={'task_uuid': task_uuid}
        )

        task = execute_synchronous_celery(sig)

        if task and task['status'] == 'SUCCESS':
            return task
        else:
            sleep(poll_frequency)
            elapsed += poll_frequency

    raise TimeoutError