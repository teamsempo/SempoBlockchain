
from server.models.user import User
from server.models.transfer_usage import TransferUsage
from server.utils.ussd.directory_listing import DirectoryListingProcessor


class UssdTasker(object):
    @staticmethod
    def send_directory_listing(user: User, chosen_transfer_usage: TransferUsage):
        processor = DirectoryListingProcessor(user, chosen_transfer_usage)
        processor.start()
