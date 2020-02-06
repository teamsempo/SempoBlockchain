from . import worker_simulator
from flask import current_app
from server import celery_app

def delay_task(task, kwargs=None, args=None, force_simulate=False):
    if current_app.config['ENABLE_SIMULATOR_MODE'] or force_simulate:
        return worker_simulator.simulate(task, kwargs, args)
    signature = celery_app.signature(task, kwargs=kwargs, args=args)
    async_result = signature.delay()
    return async_result
