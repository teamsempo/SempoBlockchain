import os
import random
import time
import uuid

from eth_keys import keys

from server.models.transfer_usage import TransferUsage
from server.models.user import User


def mock_class(orginal, substitute, monkey):
    for func_name in dir(orginal):
        if callable(getattr(orginal, func_name)) and not func_name.startswith("_"):
            func = getattr(substitute, func_name, None)

            if func is None:
                raise Exception("Function {} doesn't have a mock definition in {}!".format(func_name, substitute))

            monkey.setattr(orginal, func_name, func)


class MockMiscTasker(object):

    @staticmethod
    def set_ip_location(*args, **kwargs):
        pass


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
    def add_transaction_sync_filter(*args, **kwargs):
        return MockBlockchainTasker._blockchain_address()

    @staticmethod
    def force_third_party_transaction_sync(*args, **kwargs):
        return MockBlockchainTasker._blockchain_address()

    @staticmethod
    def retry_task(*args, **kwargs):
        pass

    @staticmethod
    def remove_all_posterior_dependencies(*args, **kwargs):
        return {
            'message': 'Removing Prior Task Dependency',
            'data': 'resp'
        }

    @staticmethod
    def remove_prior_task_dependency(*args, **kwargs):
        return {
            'message': 'Removing Prior Task Dependency',
            'data': 'resp'
        }

    @staticmethod
    def retry_failed(*args, **kwargs):
        return {
            'failed_count': 10,
            'pending_count': 2
        }

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
        return int(10e18)

    @staticmethod
    def get_allowance(*args, **kwargs):
        return int(10e18)

    @staticmethod
    def deduplicate(*args, **kwargs):
        return {
            'duplicates': 0,
            'new_deduplication_tasks': 0
        }

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


class MockUssdTasker(object):
    @staticmethod
    def send_directory_listing(user: User, chosen_transfer_usage: TransferUsage):
        pass

    @staticmethod
    def send_token(sender: User, recipient: User, amount: float, reason_str: str, reason_id: int):
        pass

    @staticmethod
    def exchange_token(sender: User, agent: User, amount: float):
        pass

    @staticmethod
    def inquire_balance(user: User):
        pass

    @staticmethod
    def fetch_user_exchange_rate(user: User):
        pass
