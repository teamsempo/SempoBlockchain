from server.models.user import User
from server.models.transfer_usage import TransferUsage
from server.utils.ussd.directory_listing import DirectoryListingProcessor


class UssdTasker(object):
    @staticmethod
    def send_directory_listing(user: User, chosen_transfer_usage: TransferUsage):
        processor = DirectoryListingProcessor(user, chosen_transfer_usage)
        processor.start()

    @staticmethod
    def send_token(user: User, amount: float, reason: str):
        print("send token for user {}, amount {}, reason {}".format(user.id, amount, reason))
        # TODO
        pass

    @staticmethod
    def exchange_token(user: User, amount: float):
        print("exchange token for user {}, amount {}".format(user.id, amount))
        # TODO
        pass

    @staticmethod
    def inquire_balance(user: User):
        print("inquire balance for user {}".format(user.id))
        # TODO
        pass

    @staticmethod
    def fetch_user_exchange_rate(user: User):
        print("fetch exchange rate for user {}".format(user.id))
        # TODO
        pass
