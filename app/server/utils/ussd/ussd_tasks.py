from server.models.token import Token
from server.models.user import User
from server.models.transfer_usage import TransferUsage
from server.utils.ussd.directory_listing_processor import DirectoryListingProcessor
from server.utils.ussd.token_processor import TokenProcessor


class UssdTasker(object):
    @staticmethod
    def send_directory_listing(user: User, chosen_transfer_usage: TransferUsage):
        processor = DirectoryListingProcessor(user, chosen_transfer_usage)
        processor.send_directory_listing()

    @staticmethod
    def send_token(sender: User, recipient: User, amount: float, reason_str: str, reason_id: int):
        TokenProcessor.send_token(sender, recipient, amount, reason_str, reason_id)

    @staticmethod
    def exchange_token(sender: User, agent: User, amount: float):
        TokenProcessor.exchange_token(sender, agent, amount)

    @staticmethod
    def inquire_balance(user: User):
        TokenProcessor.send_balance_sms(user)

    @staticmethod
    def fetch_user_exchange_rate(user: User):
        TokenProcessor.fetch_exchange_rate(user)
