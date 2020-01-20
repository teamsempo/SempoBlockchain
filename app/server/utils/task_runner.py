from . import worker_simulator
from server import celery_app

def delay_task(task, kwargs=None, args=None):
    print('sim starting')
    print(task)
    print(args)
    sim_resp = worker_simulator.simulate(task, kwargs, args)
    print('SIM RESPONSE')
    print(sim_resp)
    signature = celery_app.signature(task, kwargs=kwargs, args=args)
    print(signature)
    print(task)
    print(args)
    async_result = signature.delay()
    print('REAL RESPONSE')
    print(async_result)
    print(type(async_result))
    return async_result
