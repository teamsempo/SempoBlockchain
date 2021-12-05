from typing import Callable, List, Dict, Optional
import json
from server import executor, red, db
from uuid import uuid4
from flask import g
import config

# Only store for a week (604800 seconds)
JOB_EXPIRATION_TIME = 604800

# Generate redis key to store the results of a job
def get_job_key(user_id, func_uuid):
    return f'JOB_{user_id}_{func_uuid}'

# Get job based on user ID and func ID
def get_job_result(user_id, func_uuid):
    key = get_job_key(user_id, func_uuid)
    return red.get(key)

# Run these after any job!
def after_executor_jobs():
    db.session.close()
    db.engine.dispose()
    # Push any transactions made by an async job to the worker
    if g.pending_transactions:
        prepare_transactions_async_job()

# This is a phony executor job to be used in unthreaded environments (unit tests)
class SynchronousFunction:
    def __init__(self, func):
        self.func = func

    def submit(self, *args, **kwargs):
        func_uuid = kwargs.pop('func_uuid', None)
        if func_uuid:
            _execute_function_with_status_checks(self.func, func_uuid, *args, **kwargs)
        else:
            self.func(*args, **kwargs)

# Helper to run generators asynchronously, and store statuses in redis for the async status endpoint!
def _execute_function_with_status_checks(func, func_uuid, *args, **kwargs):
    job_key = get_job_key(g.user.id, func_uuid)
    red.set(job_key, '', ex=JOB_EXPIRATION_TIME)
    for line in func(*args, **kwargs):
        red.set(job_key, json.dumps(line), ex=JOB_EXPIRATION_TIME)

# Wrapper for executor.job
def standard_executor_job(func):
    def wrapper(*args, **kwargs):
        try:
            # Get thread-local session variables! This is very ugly.
            from server.models.organisation import Organisation
            from server.models.user import User
            if g and g.get('active_organisation'):
                g.active_organisation = db.session.query(Organisation).filter(Organisation.id == g.active_organisation.id).first() 
                db.session.merge(g.active_organisation)
                if g.active_organisation.token:
                    db.session.merge(g.active_organisation.token)
            if g and g.get('user'):
                g.user = db.session.query(User).filter(User.id == g.user.id).first() 
                db.session.merge(g.user)
            func(*args, **kwargs)
        finally:
            after_executor_jobs()
        return True
    if config.IS_TEST:
        return SynchronousFunction(func)
    return executor.job(wrapper)

# Wrapper for executor.job meant to wrap generator functions with pollable statuses.
# Automatically populates the status endpoint via _execute_function_with_status_checks!
def status_checkable_executor_job(func):
    def wrapper(*args, **kwargs):
        try:
            # Get thread-local session variables! This is very ugly.
            from server.models.organisation import Organisation
            from server.models.user import User
            if g and g.get('active_organisation'):
                g.active_organisation = db.session.query(Organisation).filter(Organisation.id == g.active_organisation.id).first() 
                db.session.merge(g.active_organisation)
                db.session.merge(g.active_organisation.token)
            if g and g.get('user'):
                g.user = db.session.query(User).filter(User.id == g.user.id).first() 
                db.session.merge(g.user)

            func_uuid = kwargs.pop('func_uuid')
            _execute_function_with_status_checks(func, func_uuid, *args, **kwargs)
        finally:
            after_executor_jobs()
        return True
    if config.IS_TEST:
        return SynchronousFunction(func)
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

@standard_executor_job
def bulk_process_transactions(transactions):
    # This is very ugly, but required to get a thread-local CreditTransfer/Exchange instance
    from server.models.credit_transfer import CreditTransfer
    from server.models.exchange import Exchange
    for transaction, queue in transactions:
        if isinstance(transaction, CreditTransfer):
            transaction = db.session.query(CreditTransfer).filter(CreditTransfer.id == transaction.id).first()
        else:
            transaction = db.session.query(Exchange).filter(Exchange.id == transaction.id).first()
        transaction.send_blockchain_payload_to_worker(queue=queue)

def prepare_transactions_async_job():
    add_after_request_executor_job(bulk_process_transactions, args=[g.pending_transactions])
    g.pending_transactions = []
