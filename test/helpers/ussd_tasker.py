from server.models.user import User
from server.models.transfer_usage import TransferUsage


class MockUssdTasker(object):
    @staticmethod
    def send_directory_listing(user: User, chosen_transfer_usage: TransferUsage):
        pass
