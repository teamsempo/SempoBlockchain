eth_worker_name = 'eth_manager'
celery_tasks_name = 'celery_tasks'
eth_endpoint = lambda endpoint: f'{eth_worker_name}.{celery_tasks_name}.{endpoint}'

def execute_synchronous_task(signature):
    async_result = signature.delay()

    try:
        response = async_result.get(timeout=2, propagate=True, interval=0.3)
    except Exception as e:
        raise e
    finally:
        async_result.forget()

    return response
