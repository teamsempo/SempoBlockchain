from typing import Callable, List, Dict, Optional
import json
from server import executor, red, db
from uuid import uuid4
from flask import g

# Only store for a week (604800 seconds)
JOB_EXPIRATION_TIME = 604800

def get_job_key(user_id, func_uuid):
    return f'JOB_{user_id}_{func_uuid}'

def standard_executor_job(func):
    # Wrapper for executor.job which makes prevents a glut of unclosed sessions/threads
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        db.session.close()
        db.engine.dispose()
        return True
    return executor.job(wrapper)

def status_checkable_executor_job(func):
    def wrapper(*args, **kwargs):
        func_uuid = kwargs.pop('func_uuid')
        job_key = get_job_key(g.user.id, func_uuid)
        red.set(job_key, '', ex=JOB_EXPIRATION_TIME)
        for line in func(*args, **kwargs):
            red.set(job_key, json.dumps(line), ex=JOB_EXPIRATION_TIME)
        db.session.close()
        db.engine.dispose()
        return True
    return executor.job(wrapper)


def add_after_request_executor_job(
        fn: Callable,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None
):
    """
    Utility function for adding executor jobs that need to be submitted AFTER a request has completed
    (generally speaking, to avoid potential race conditions).

    :param fn: the executor decorated function that will be submitted, eg do_foo NOT do_foo.submit
    :param args: function arguments
    :param kwargs: function keyword arguments
    :return:
    """
    args = args or []
    kwargs = kwargs or {}
    # If after_request has already started, adding to the executor_jobs list is useless!
    # In that case, just submit the job right away
    if not g.is_after_request:
        g.executor_jobs.append((fn, args, kwargs))
    else:
        fn.submit(*args, **kwargs)
    
def add_after_request_checkable_executor_job(fn, args=None, kwargs=None):
    """
    Like add_after_request_executor_job, but injects and returns a UUID into kwargs for 
    `status_checkable_executor_job`
    """
    func_uuid = str(uuid4())
    kwargs = {} if not kwargs else kwargs
    kwargs['func_uuid'] = func_uuid
    add_after_request_executor_job(fn, args, kwargs)
    return func_uuid
