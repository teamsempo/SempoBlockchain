from . import worker_simulator
from flask import current_app
from server import celery_app

def delay_task(task, kwargs=None, args=None, force_simulate=False, queue='high-priority', task_uuid=None):
    print("TASK RUNNER!")
    print((task, kwargs, args))
    print("TASK RUNNER!")

    if current_app.config['ENABLE_SIMULATOR_MODE'] or force_simulate:
        return worker_simulator.simulate(task, kwargs, args, queue)
    signature = celery_app.signature(task, kwargs=kwargs, args=args)
    return signature.apply_async(queue=queue, task_id=task_uuid)
