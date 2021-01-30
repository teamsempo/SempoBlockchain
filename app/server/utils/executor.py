from typing import Callable, List, Dict, Optional
from functools import wraps
from server import executor, red
from uuid import uuid4

from flask import g

JOB_NAME_PREFIX = 'JOB'
def status_checkable_executor_job(func):
    def wrapper(*args, **kwargs):
        func_uuid = kwargs.pop('func_uuid')
        red.set(f'{JOB_NAME_PREFIX}{func_uuid}',)
        for line in func(*args, **kwargs):
            print(line)
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

    g.executor_jobs.append((fn, args, kwargs))

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