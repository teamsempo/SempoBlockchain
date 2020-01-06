import time
import random
import os
from eth_keys import keys
import uuid


class MockBlockchainTasker(object):

    @staticmethod
    def get_blockchain_task(*args, **kwargs):
        return {
            'status': 'SUCCESS',
            'dependents': []
        }

    @staticmethod
    def await_task_success(*args, **kwargs):

        time.sleep(random.random())
        return MockBlockchainTasker.get_blockchain_task()

    @staticmethod
    def retry_task(*args, **kwargs):
        pass

    @staticmethod
    def create_blockchain_wallet(*args, **kwargs):
        return MockBlockchainTasker._blockchain_address()

    @staticmethod
    def send_eth(*args, **kwargs):
        return MockBlockchainTasker._generic_task()

    @staticmethod
    def deploy_contract(*args, **kwargs):
        return MockBlockchainTasker._generic_task()

    @staticmethod
    def make_token_transfer(*args, **kwargs):
        return MockBlockchainTasker._generic_task()

    @staticmethod
    def make_approval(*args, **kwargs):
        return MockBlockchainTasker._generic_task()

    @staticmethod
    def make_liquid_token_exchange(*args, **kwargs):
        return MockBlockchainTasker._generic_task()

    @staticmethod
    def get_conversion_amount(from_amount, *args, **kwargs):
        return random.random() * from_amount

    @staticmethod
    def get_token_decimals(*args, **kwargs):
        return 18

    @staticmethod
    def get_wallet_balance(*args, **kwargs):
        return 100

    @staticmethod
    def deploy_exchange_network(*args, **kwargs):
        return MockBlockchainTasker._blockchain_address()

    @staticmethod
    def deploy_and_fund_reserve_token(*args, **kwargs):
        return MockBlockchainTasker._blockchain_address()

    @staticmethod
    def deploy_smart_token(*args, **kwargs):
        return {
            'smart_token_address': MockBlockchainTasker._blockchain_address(),
            'subexchange_address': MockBlockchainTasker._blockchain_address()
        }

    @staticmethod
    def topup_wallet_if_required(*args, **kwargs):
        return MockBlockchainTasker._generic_task()

    @staticmethod
    def _generic_task():
        return str(uuid.uuid4())

    @staticmethod
    def _blockchain_address():
        return keys.PrivateKey(os.urandom(32)).public_key.to_checksum_address()
