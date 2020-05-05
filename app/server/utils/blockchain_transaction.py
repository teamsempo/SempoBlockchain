from server.exceptions import BlockchainError
from server import celery_app
import sentry_sdk

def get_usd_to_satoshi_rate():

    blockchain_task = celery_app.signature('worker.celery_tasks.get_usd_to_satoshi_rate')
    # TODO: Convert to task_runner
    result = blockchain_task.apply_async()

    try:
        conversion_rate = result.wait(timeout=3, propagate=True, interval=0.5)

    except Exception as e:
        print(e)
        sentry_sdk.capture_exception(e)
        raise BlockchainError("Blockchain Error")

    finally:
        result.forget()

    return conversion_rate