from ethereum import utils
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth

import config

from worker.bitcoin_processor import BitcoinProcessor
from worker.ethereum_processor import MintableERC20Processor, UnmintableERC20Processor, PreBlockchainError
from worker import celery_app
from worker.ABIs import standard_erc20_abi, ccv_abi, mintable_abi, dai_abi
# from worker import rekognition
# from worker import geolocation
# from worker import ip_location
# from worker import trulioo

from celery.exceptions import MaxRetriesExceededError

ERC20_config = {}
ERC20_config['ethereum_chain_id'] = config.ETH_CHAIN_ID
ERC20_config['http_provider'] = config.ETH_HTTP_PROVIDER
ERC20_config['websocket_provider'] = config.ETH_WEBSOCKET_PROVIDER
ERC20_config['gas_price_gwei'] = config.ETH_GAS_PRICE
ERC20_config['gas_limit'] = config.ETH_GAS_LIMIT

ETH_CHECK_TRANSACTION_RETRIES = config.ETH_CHECK_TRANSACTION_RETRIES
ETH_CHECK_TRANSACTION_RETRIES_TIME_LIMIT = config.ETH_CHECK_TRANSACTION_RETRIES_TIME_LIMIT
ETH_CHECK_TRANSACTION_BASE_TIME = config.ETH_CHECK_TRANSACTION_BASE_TIME

BITCOIN_CHECK_TRANSACTION_BASE_TIME = config.BITCOIN_CHECK_TRANSACTION_BASE_TIME
BITCOIN_CHECK_TRANSACTION_RETRIES = config.BITCOIN_CHECK_TRANSACTION_RETRIES

if config.IS_USING_BITCOIN:
    blockchain_processor = BitcoinProcessor(config.BITCOIN_MASTER_WALLET_WIF, config.IS_BITCOIN_TESTNET)

elif config.ETH_CONTRACT_TYPE == 'mintable':
    print('~~~USING MINTABLE~~~')

    ERC20_config['contract_abi_string'] = mintable_abi.abi
    ERC20_config['contract_address'] = config.ETH_CONTRACT_ADDRESS
    ERC20_config['contract_owner_private_key'] = config.ETH_OWNER_PRIVATE_KEY
    expected_contract_name = config.ETH_CONTRACT_NAME

    blockchain_processor = MintableERC20Processor(**ERC20_config)
    blockchain_processor.check_contract_name(expected_contract_name)

elif config.ETH_CONTRACT_TYPE == 'ccv':
    print('~~~USING CCV~~~')
    ERC20_config['contract_abi_string'] = ccv_abi.abi
    ERC20_config['contract_address'] = config.ETH_CONTRACT_ADDRESS
    ERC20_config['master_wallet_private_key'] = config.MASTER_WALLET_PRIVATE_KEY
    ERC20_config['withdraw_to_address'] = config.WITHDRAW_TO_ADDRESS

    blockchain_processor = UnmintableERC20Processor(**ERC20_config)

else:
    print('~~~USING DAI/External~~~')
    ERC20_config['contract_abi_string'] = dai_abi.abi
    ERC20_config['contract_address'] = config.ETH_CONTRACT_ADDRESS
    ERC20_config['master_wallet_private_key'] = config.MASTER_WALLET_PRIVATE_KEY
    ERC20_config['force_eth_disbursement_amount'] = config.FORCE_ETH_DISBURSEMENT_AMOUNT
    ERC20_config['withdraw_to_address'] = config.WITHDRAW_TO_ADDRESS

    blockchain_processor = UnmintableERC20Processor(**ERC20_config)

# rekogniser = rekognition.Rekogniser()


# def attempt_atomic_celery_task(self, task, *args, **kwargs):
#     try:
#         return task(*args, **kwargs)
#
#     except PreBlockchainError:
#
#     # except Exception as e:
#     #     print(e)
#     #     print('retrying')
#     #     self.retry(countdown=general_retry_base_rate ** self.request.retries)

def chain_with_error(*args, **kwargs):
    return

@celery_app.task
def log_error(request, exc, traceback, credit_transfer_id):
    if type(exc) is PreBlockchainError:
        result = exc.args[0]
        result['credit_transfer_id'] = credit_transfer_id
        blockchain_processor.send_blockchain_result_to_app(result)


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


@celery_app.task(bind=True, max_retries=BITCOIN_CHECK_TRANSACTION_RETRIES, soft_time_limit=300)
def check_transaction_status_in_pool(self, check_sent_to_pool_result):

    transaction_hash, blockchain_transaction_ids = check_sent_to_pool_result

    try:
        success = blockchain_processor.check_transaction_status_in_pool(transaction_hash, blockchain_transaction_ids)

        if not success:
            self.retry(countdown=BITCOIN_CHECK_TRANSACTION_BASE_TIME * 2 ** self.request.retries)

    except MaxRetriesExceededError:

        submitted_date = datetime.utcnow()

        for transaction_id in blockchain_transaction_ids:
            response = blockchain_processor.put_blockchain_result_to_app({
                'transaction_id': transaction_id,
                'status': 'FAILED',
                'message': 'Timeout in pool',
                'transaction_type': 'transfer',
                'submitted_date': submitted_date.isoformat()
            })

@celery_app.task()
def print_foo():
    print('foo')

@celery_app.task()
def find_new_ouputs():
    blockchain_processor.find_new_outputs()

@celery_app.task()
def find_new_external_inbounds():
    blockchain_processor.find_new_external_inbounds()

# @celery_app.task()
# def geolocate_address(geo_task):
#     app_host = config.APP_HOST
#
#     geo_result = geolocation.parse_geo_task(geo_task)
#
#     if geo_result.get('status') == 'success':
#         r = requests.post(app_host + '/api/geolocation/',
#                           json={'user_id': geo_result.get('user_id'),
#                                 'lat': geo_result.get('lat'),
#                                 'lng': geo_result.get('lng')
#                                 },
#                           auth=HTTPBasicAuth(config.BASIC_AUTH_USERNAME,
#                                              config.BASIC_AUTH_PASSWORD))
#
#
# @celery_app.task()
# def ip_location(ip_task):
#     app_host = config.APP_HOST
#
#     ip_result = ip_location.ip_location_task(ip_task)
#
#     if ip_result.get('status') == 'success':
#         r = requests.post(app_host, '/api/ip_address_location/',
#                           json={'ip_address_id': ip_result.get('ip_address_id'),
#                                 'country': ip_result.get('country'),
#                                 },
#                           auth=HTTPBasicAuth(config.BASIC_AUTH_USERNAME,
#                                              config.BASIC_AUTH_PASSWORD))
#
#
# @celery_app.task()
# def check_for_duplicate_person(image_name, image_id):
#
#     app_host = config.APP_HOST
#
#     rekognised_faces = rekogniser.facial_recognition(image_name)
#
#     if len(rekognised_faces) > 0:
#         r = requests.put(app_host + '/api/recognised_face/',
#                          json={'image_id': image_id, 'recognised_faces': rekognised_faces},
#                          auth=HTTPBasicAuth(config.BASIC_AUTH_USERNAME,
#                                             config.BASIC_AUTH_PASSWORD)
#                          )
#
#     upload_resp = rekogniser.upload_face(image_name, image_id)
#
#     if upload_resp['success']:
#         r = requests.post(app_host + '/api/recognised_face/',
#                           json={'image_id': image_id, 'roll': upload_resp['roll']},
#                           auth=HTTPBasicAuth(config.BASIC_AUTH_USERNAME,
#                                              config.BASIC_AUTH_PASSWORD)
#                           )
# #
# #
# # @celery_app.task()
# # def trulioo_verification(trulioo_task):
# #     app_host = config.APP_HOST
# #
# #     trulioo_result = trulioo.trulioo_task(trulioo_task)
# #
# #     if trulioo_result:
# #         r = requests.put(app_host, '/api/kyc_application/',
# #                           json=trulioo_result,
# #                           auth=HTTPBasicAuth(config.BASIC_AUTH_USERNAME,
# #                                              config.BASIC_AUTH_PASSWORD))
