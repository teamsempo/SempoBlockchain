from . import eth_worker_simulator
from server import celery_app

def delay_task(task, args):
    print('sim starting')
    eth_worker_simulator.simulate(task, args)
    signature = celery_app.signature(task, kwargs=args)
    print(signature)
    print(task)
    print(args)
    async_result = signature.delay()
    return async_result
