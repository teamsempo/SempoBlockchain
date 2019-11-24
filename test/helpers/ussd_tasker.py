from server.models.user import User
from server.models.transfer_usage import TransferUsage


class MockUssdTasker(object):
    @staticmethod
    def send_directory_listing(user: User, chosen_transfer_usage: TransferUsage):
        pass

    @staticmethod
    def send_token(user: User, amount: float, reason: str):
        pass

    @staticmethod
    def exchange_token(user: User, amount: float):
        pass

    @staticmethod
    def inquire_balance(user: User):
        pass

    @staticmethod
    def fetch_user_exchange_rate(user: User):
        pass
