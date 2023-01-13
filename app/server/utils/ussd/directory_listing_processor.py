from sqlalchemy import text
from sqlalchemy.sql import func

from server import db
from server.utils.phone import send_translated_message
from server.models.user import User
from server.models.transfer_account import TransferAccount
from server.models.transfer_usage import TransferUsage
from server.models.credit_transfer import CreditTransfer
from server.utils.user import default_token

from server.constants import NUMBER_OF_DIRECTORY_LISTING_RESULTS



def user_directory_listing(user: User) -> str:
    bio = next(filter(lambda x: x.key == 'bio', user.custom_attributes), None)
    if bio is None:
        return user.phone
    else:
        return f"{user.phone} {bio.value}"


class DirectoryListingProcessor(object):
    def __init__(self, user: User, transfer_usage: TransferUsage):
        self.recipient = user
        self.selected_business_category = transfer_usage

    def send_sms(self, message_key, **kwargs):
        # if we use directory listing similarly for other countries later, can generalize country to init
        send_translated_message(self.recipient, "ussd.sempo.{}".format(message_key), **kwargs)
        
    # get users to be appended to message for the directory listing matching recipient's search criteria.
    def get_directory_listing_users(self):
        token_id = default_token(self.recipient).id

        """
        SEARCH CRITERIA:
            - users matching recipient provided business category
            - users with the recipient's token
            - users who are opted in to market [custom_attribute 'market_enabled' has value true]
            - order query by transaction count and limit to top 5 transacting users
        """
        count_list = (
            db.session.query(
                User.id,
                func.count(CreditTransfer.id).label('count'))
            .execution_options(show_all=True)
            .join(User.credit_receives)
            .join(TransferAccount, TransferAccount.id == User.default_transfer_account_id)
            .group_by(User.id)
            .filter(TransferAccount.token_id == token_id)
            .filter(User.is_market_enabled == True)
            .filter(User.business_usage_id == self.selected_business_category.id)
            .filter(CreditTransfer.transfer_status == 'COMPLETE')
            .limit(NUMBER_OF_DIRECTORY_LISTING_RESULTS).all()
        )

        user_ids = list(map(lambda x: x[0], count_list))

        count_based_users = list(map(lambda x: User.query.execution_options(show_all=True).get(x), user_ids))

        shortfall = NUMBER_OF_DIRECTORY_LISTING_RESULTS - len(count_based_users)

        matching_category_users = []
        if shortfall > 0:
            matching_category_users = (
                User.query
                    .execution_options(show_all=True)
                    .join(TransferAccount, TransferAccount.id == User.default_transfer_account_id)
                    .filter(User.id.notin_(user_ids))
                    .filter(TransferAccount.token_id == token_id)
                    .filter(User.is_market_enabled == True)
                    .filter(User.business_usage_id == self.selected_business_category.id)
                    .limit(shortfall).all()
            )

        return count_based_users + matching_category_users

    def get_business_category_translation(self):
        try:
            if self.recipient.preferred_language and self.selected_business_category.translations:
                return self.selected_business_category.translations[self.recipient.preferred_language]
            else:
                return self.selected_business_category.name
        except KeyError:
            return self.selected_business_category.name

    def send_directory_listing(self):
        transfer_account = self.recipient.default_transfer_account
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
