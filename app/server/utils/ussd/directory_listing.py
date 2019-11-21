import threading

from server import message_processor
from server.utils.i18n import i18n_for
from server.models.user import User
from server.models.custom_attribute_user_storage import CustomAttributeUserStorage
from server.models.transfer_usage import TransferUsage
from server.models.transfer_account import TransferAccount


def user_directory_listing(user):
    # TODO: add custom attribute bio
    return f"{user.phone}"


class DirectoryListingProcessor(threading.Thread):
    def __init__(self, user: User, transfer_usage: TransferUsage):
        self.recipient = user
        self.selected_business_category = transfer_usage

        threading.Thread.__init__(self)
        self.runnable = self.send_directory_listing
        self.daemon = True

    def run(self):
        self.runnable()

    def send_sms(self, message_key, **kwargs):
        # if we use directory listing similarly for other countries later, can generalize country to init
        message = i18n_for(self.recipient, "ussd.kenya.{}".format(message_key), **kwargs)
        message_processor.send_message(self.recipient.phone, message)

    # get users to be appended to message for the directory listing matching recipient's search criteria.
    def get_directory_listing_users(self):
        transfer_account = TransferAccount.query.get(self.recipient.default_transfer_account_id)
        token_id = transfer_account.token_id

        """
        SEARCH CRITERIA:
            - users matching recipient provided business category
            - users with the recipient's token
            - users who are opted in to market [custom_attribute 'market_enabled' has value true]
            - order query by transaction count and limit to top 5 transacting users
        """
        users = User.query.join(CustomAttributeUserStorage).join(TransferAccount).filter(
            User.business_usage_id == self.selected_business_category.id,
            TransferAccount.token_id == token_id,
            CustomAttributeUserStorage.name == 'market_enabled',
            CustomAttributeUserStorage.value == True).order_by(
            User.transaction_count
        ).limit(5).all()

        return users

    def get_business_category_translation(self):
        try:
            translation = self.selected_business_category.translations[self.recipient.preferred_language]
            return translation
        except KeyError:
            return self.selected_business_category.name

    def send_directory_listing(self):
        transfer_account = TransferAccount.query.get(self.recipient.default_transfer_account_id)
        token = transfer_account.token

        # find users who fit recipient's selected business category and are opted in for marketplace
        directory_listing_users = self.get_directory_listing_users()

        # get business category in appropriate language for user if available
        user_business_category = self.get_business_category_translation()

        if len(directory_listing_users) > 0:
            # define list store users matching search criteria
            directory_listing_users_list = map(lambda x: user_directory_listing(x), directory_listing_users)

            # convert list of users matching search criteria to string to add to send_directory_listing_message
            message_appendage = "\n".join(directory_listing_users_list)

            self.send_sms(
                'send_directory_listing_message',
                community_token_name=token.name,
                business_type=user_business_category,
                directory_listing_users=message_appendage
            )
        else:
            self.send_sms('no_directory_listing_found_message')
