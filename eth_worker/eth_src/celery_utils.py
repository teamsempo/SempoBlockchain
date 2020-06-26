from time import sleep

from celery import signature

celery_tasks_name = 'celery_tasks'
eth_endpoint = lambda endpoint: f'{celery_tasks_name}.{endpoint}'
import config

def execute_synchronous_celery(signature):
    async_result = signature.delay()
    try:
        response = async_result.get(
            timeout=config.SYNCRONOUS_TASK_TIMEOUT,
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


def await_blockchain_success_evil(task_uuid, timeout=None, poll_frequency=0.5):
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