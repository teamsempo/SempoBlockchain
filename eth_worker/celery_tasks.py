from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
from celery.exceptions import MaxRetriesExceededError

from eth_worker import celery_app

@celery_app.task()
def print_foo():
    print('foo')


ETH_CHECK_TRANSACTION_RETRIES = 4

from eth_worker import ERC20_config
from eth_worker.processor import TransactionProcessor, ContractRegistry, PreBlockchainError

registry = ContractRegistry(w3=ERC20_config['w3'])
registry.register_contract(ERC20_config['contract_address'],
                           ERC20_config['contract_abi_string'],
                           'Dai Stablecoin v1.0')

blockchain_processor = TransactionProcessor(**ERC20_config)


def chain_with_error(*args, **kwargs):
    return

@celery_app.task
def log_error(request, exc, traceback, credit_transfer_id):
    if type(exc) is PreBlockchainError:
        result = exc.args[0]
        result['credit_transfer_id'] = credit_transfer_id
        # blockchain_processor.send_blockchain_result_to_app(result)

@celery_app.task(bind=True, max_retries=3, soft_time_limit=300)
def complete_blockchain_task(self, contract, function, args=None, kwargs=None):

    function_obj = registry.get_contract_function(contract,function)



    tt = 5


@celery_app.task(bind=True, max_retries=3, soft_time_limit=300)
def make_blockchain_transaction(self, blockchain_payload):
    return blockchain_processor.parse_blockchain_task(blockchain_payload)


@celery_app.task(bind=True, max_retries=3, soft_time_limit=300)
def disburse_funds(self, transfer_amount, recipient_address, credit_transfer_id):
    return blockchain_processor.disburse_funds_async(transfer_amount, recipient_address, credit_transfer_id)

@celery_app.task(bind=True, max_retries=3, soft_time_limit=300)
def transfer_credit(self, transfer_amount, sender_address, recipient_address, credit_transfer_id):
    return blockchain_processor.transfer_credit_async(transfer_amount, sender_address, recipient_address, credit_transfer_id)

@celery_app.task(bind=True, max_retries=3, soft_time_limit=300)
def make_withdrawal(self, transfer_amount, sender_address, recipient_address, credit_transfer_id):
    return blockchain_processor.withdrawal_async(transfer_amount, sender_address, recipient_address, credit_transfer_id)

@celery_app.task(bind=True, max_retries=3, soft_time_limit=300)
def load_ether(self, recipient_address, gas_required, gas_price):
    return  blockchain_processor.load_ether_async(recipient_address, gas_required, gas_price)
    # return attempt_atomic_celery_task(
    #     self,
    #     blockchain_processor.load_ether_async,
    #     recipient_address
    # )

@celery_app.task(bind=True, max_retries=3, soft_time_limit=300)
def approve_master_for_transfers(self, account_to_approve_encoded_pk, gas_required, gas_price):
    return blockchain_processor.approve_master_for_transfers_async(account_to_approve_encoded_pk, gas_required, gas_price)
    # return attempt_atomic_celery_task(
    #     self,
    #     blockchain_processor.approve_master_for_transfers_async(account_to_approve_encoded_pk)
    # )

@celery_app.task(bind=True, max_retries=3, soft_time_limit=300)
def get_master_balance(self):
    return blockchain_processor.get_master_wallet_balance_async()

@celery_app.task(bind=True, max_retries=3, soft_time_limit=300)
def get_usd_to_satoshi_rate(self):
    return blockchain_processor.get_usd_to_satoshi_rate()

@celery_app.task(bind=True, max_retries=ETH_CHECK_TRANSACTION_RETRIES, soft_time_limit=300)
def create_transaction_response(self, previous_result, credit_transfer_id):

    def transaction_response_countdown():
        t = lambda retries: ETH_CHECK_TRANSACTION_BASE_TIME*2**retries

        # If the system has been longer than the max retry period
        if previous_result:
            submitted_at = datetime.strptime(previous_result['submitted_date'], "%Y-%m-%d %H:%M:%S.%f")
            if (datetime.utcnow() - submitted_at).total_seconds() > ETH_CHECK_TRANSACTION_RETRIES_TIME_LIMIT:
                if self.request.retries != self.max_retries:
                    self.request.retries = self.max_retries - 1

                return 0

        return t(self.request.retries)

    try:
        try:
            result = blockchain_processor.create_transaction_response(previous_result['transaction_hash'])

        except Exception as e:
            print(e)
            self.retry(countdown=transaction_response_countdown())

        else:
            result = {**previous_result, **result, 'credit_transfer_id': credit_transfer_id}

            blockchain_processor.send_blockchain_result_to_app(result)

            if result['status'] == 'PENDING':
                self.retry(countdown=transaction_response_countdown())

            return result

    except MaxRetriesExceededError as e:

        result = {**previous_result,
                  'status': 'FAILED',
                  'message': 'timeout',
                  'credit_transfer_id': credit_transfer_id}

        blockchain_processor.send_blockchain_result_to_app(result)

        raise e


@celery_app.task()
def check_if_valid_address(address):
    return blockchain_processor.check_if_valid_address(address)


@celery_app.task(bind=True, soft_time_limit=300)
def get_next_transaction_outputs(self):
    return blockchain_processor.get_next_transaction_outputs()

@celery_app.task(bind=True, max_retries=5, soft_time_limit=300)
def resilient_bitcoin_send(self, transaction_data):

    outputs = transaction_data['outputs']
    credit_transfer_ids = transaction_data['credit_transfer_ids']

    try:
        transaction_hash = blockchain_processor.send_bitcoin_transaction(outputs)
        return (transaction_hash, credit_transfer_ids)

    except ConnectionError:
        self.retry(countdown=2 * 2 ** self.request.retries)

    except Exception as e:
        submitted_date = datetime.datetime.utcnow()

        for credit_transfer_id in credit_transfer_ids:
            response = blockchain_processor.post_blockchain_result_to_app({
                'credit_transfer_id': credit_transfer_id,
                'status': 'FAILED',
                'message': str(e),
                'transaction_type': 'transfer',
                'submitted_date': submitted_date.isoformat()
            })

        raise


@celery_app.task(bind=True, max_retries=7, soft_time_limit=300)
def check_whether_transaction_sent_to_pool(self, submit_result):
    transaction_hash, credit_transfer_ids = submit_result

    try:
        check_sent_to_pool_result = (
            blockchain_processor.check_whether_transaction_sent_to_pool(transaction_hash, credit_transfer_ids)
        )

        if not check_sent_to_pool_result:
            raise Exception("Not found in pool")
        else:
            return check_sent_to_pool_result

    except Exception as e:
        # This is so we can log the underlying error rather than just getting a MaxRetriesExceededError
        if self.request.retries < self.max_retries - 1:
            self.retry(countdown=2 * 2 ** self.request.retries)
        else:
            submitted_date = datetime.utcnow()

            for credit_transfer_id in credit_transfer_ids:
                response = blockchain_processor.post_blockchain_result_to_app({
                    'credit_transfer_id': credit_transfer_id,
                    'status': 'FAILED',
                    'message': 'Failed to add to pool: ' + str(e),
                    'transaction_type': 'transfer',
                    'submitted_date': submitted_date.isoformat(),
                    'force_transaction_creation': True
                })

            raise e

@celery_app.task()
def find_new_ouputs():
    blockchain_processor.find_new_outputs()

@celery_app.task()
def find_new_external_inbounds():
    blockchain_processor.find_new_external_inbounds()