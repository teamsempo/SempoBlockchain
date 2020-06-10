from typing import Callable, List, Dict, Optional

from flask import g


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
