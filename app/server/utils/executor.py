from typing import Callable, List, Dict, Optional
import json
from server import red, db
from uuid import uuid4
from flask import g, current_app

# Only store for a week (604800 seconds)
JOB_EXPIRATION_TIME = 604800

# Generate redis key to store the results of a job
def get_job_key(user_id, func_uuid):
    return f'JOB_{user_id}_{func_uuid}'

# Get job based on user ID and func ID
def get_job_result(user_id, func_uuid):
    key = get_job_key(user_id, func_uuid)
    return red.get(key)

class SynchronousFunction:
    def __init__(self, func):
        self.func = func

    def submit(self, *args, **kwargs):
        func_uuid = kwargs.pop('func_uuid', None)
        if func_uuid:
            _execute_function_with_status_checks(self.func, func_uuid, *args, **kwargs)
        else:
            self.func(*args, **kwargs)

# Helper to run generators after a request returns, and store statuses in redis for the async status endpoint!
def _execute_function_with_status_checks(func, func_uuid, *args, **kwargs):
    job_key = get_job_key(g.user.id, func_uuid)
    red.set(job_key, '', ex=JOB_EXPIRATION_TIME)
    for line in func(*args, **kwargs):
        red.set(job_key, json.dumps(line), ex=JOB_EXPIRATION_TIME)

# Wrapper for executor.job
def standard_executor_job(func):
    return SynchronousFunction(func)

# Wrapper for executor.job meant to wrap generator functions with pollable statuses.
# Automatically populates the status endpoint via _execute_function_with_status_checks!
def status_checkable_executor_job(func):
    return SynchronousFunction(func)


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
    # If after_request has already started, adding to the deferred_jobs list is useless!
    # In that case, just submit the job right away
    if not g.is_after_request:
        g.deferred_jobs.append((fn, args, kwargs))
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

# Run these after any job!
def after_deferred_jobs():
    if g.pending_transactions:
        bulk_process_transactions()

def bulk_process_transactions():
    # This is very ugly, but required to get a thread-local CreditTransfer/Exchange instance
    from server.models.credit_transfer import CreditTransfer
    from server.models.exchange import Exchange
    from server.utils import pusher_utils
    for transaction, queue in g.pending_transactions:
        pusher_transactions = []
        if isinstance(transaction, CreditTransfer):
            transaction = db.session.query(CreditTransfer).filter(CreditTransfer.id == transaction.id).first()
        else:
            transaction = db.session.query(Exchange).filter(Exchange.id == transaction.id).first()
        transaction.send_blockchain_payload_to_worker(queue=queue)
        pusher_transactions.append(transaction)
        g.pending_transactions = []
    if not current_app.config['IS_TEST']:
        pusher_utils.push_admin_credit_transfer([txn for txn in pusher_transactions])
