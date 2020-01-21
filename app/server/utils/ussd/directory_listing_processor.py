import threading
from sqlalchemy import text

from server import message_processor, db
from server.utils.i18n import i18n_for
from server.models.user import User
from server.models.transfer_usage import TransferUsage
from server.models.transfer_account import TransferAccount
from server.utils.user import default_token


def user_directory_listing(user: User) -> str:
    bio = next(filter(lambda x: x.name == 'bio', user.custom_attributes), None)
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
        message = i18n_for(self.recipient, "ussd.kenya.{}".format(message_key), **kwargs)
        message_processor.send_message(self.recipient.phone, message)

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
        # users with no credit transfers still have count of 1 since left join... not great but it works
        sql = text('''
            SELECT *, COUNT(*) co FROM
                (SELECT u.id FROM "user" u
                LEFT JOIN "credit_transfer" c ON u.id = c.recipient_user_id 
                LEFT JOIN "custom_attribute_user_storage" ca ON ca.user_id = u.id
                INNER JOIN "transfer_account" tr ON u.default_transfer_account_id = tr.id
                INNER JOIN "token" tk ON tr.token_id = tk.id
                WHERE u.business_usage_id = {} 
                AND u.id != {}
                AND tk.id = {}
                AND (c.transfer_status = 'COMPLETE' OR c.transfer_status IS NULL)
                AND (ca.name = 'market_enabled' OR ca.name IS NULL)
                AND (ca.value::text = 'true' OR ca.value IS NULL)
                ORDER BY c.updated DESC
                LIMIT 100) C
            GROUP BY id 
            ORDER BY co DESC
            LIMIT 5
        '''.format(self.selected_business_category.id, self.recipient.id, token_id))
        result = db.session.execute(sql)
        ids = [row[0] for row in result]

        # TODO: how to convert from id to user while presChoose Market Categoryerving order?
        return list(map(lambda x: User.query.execution_options(show_all=True).get(x), ids))

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
