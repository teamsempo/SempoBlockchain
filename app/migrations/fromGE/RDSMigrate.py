import MySQLdb
import secrets as SECRETS
import pprint
from sqlalchemy import create_engine

from server.models.user import User
from server import db
from server.utils.user import create_transfer_account_user
from server.utils.user import set_custom_attributes
from server.models.custom_attribute_user_storage import CustomAttributeUserStorage



class RDSMigrate:
    '''
    Access to a MySQL relational database in AWS. This class will be
    used to migrate the 2 databases
    '''

    def __init__(self):
        timeout = 120
        print('RDSMigrate: Creating a connection, with a %d sec timeout.' % timeout)
        self.connection = MySQLdb.connect(host=SECRETS.host,
                                          db=SECRETS.name,
                                          user=SECRETS.user,
                                          port=SECRETS.port,
                                          password=SECRETS.password,
                                          connect_timeout=timeout)

        if not self.connection:
            raise RuntimeError('Could not connect to database')
        else:
            print('DB connection successfully created.  Yeah us.')

    def migrate(self):
        self.migrateUsers()
   
    def migrateUsers(self):
        list_of_phones = self.get_phones_from_sempo()
        print(list_of_phones)
        self.get_new_users_from_GE(list_of_phones)

    def get_phones_from_sempo(self):
        result = users = User.query.filter(User.phone.isnot(None)).with_entities(User.phone).execution_options(
                show_all=True).all()
        return [r[0] for r in result]

    def get_new_users_from_GE(self, list_of_phones):
        print('Getting new users from GE')
        with self.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            format_strings = ','.join(['%s'] * len(list_of_phones))
            print('format_strings', format_strings)
            cmd = """SELECT * FROM users
                INNER JOIN community_tokens ON users.community_token_id=community_tokens.id
                INNER JOIN business_categories ON users.business_category_id=business_categories.id
                WHERE phone NOT IN (%s) LIMIT 1
            """
            cursor.execute(cmd % format_strings, tuple(list_of_phones))
            null_count = 0
            a = 0
            users = cursor.fetchall()
            print('Fetched {} users'.format(len(users)))
            for user in users:
                pprint.pprint(user)
                self.insert_user(user)

    def insert_user(self, ge_user):
        print('Insert user: ', ge_user['first_name'])
        is_beneficiary = True  # How can I identify this from GE user?

        # transer_account
        sempo_user = create_transfer_account_user(
            blockchain_address=ge_user['contract_address'],
            first_name=ge_user['first_name'],
            last_name=ge_user['last_name'],
            phone=ge_user['phone'],
            preferred_language=ge_user['preferred_language'],
            # organisation=user['organisation'],
            is_beneficiary=is_beneficiary,
            is_vendor=not is_beneficiary,
            # token=ge_user['token_identifier'],
        )

        sempo_user.custom_attributes = self.get_custom_attributes(ge_user)

        

        print('Succesfully inserted', sempo_user.first_name)
        db.session.commit()

    def get_custom_attributes(self, ge_user):
        wanted_custom_attributes = [
            'bio',
            'gender',
            'market_enabled',
            'phone_listed'
            ]
        custom_attributes = []
        for attribute in wanted_custom_attributes:
            if attribute in ge_user:
                # custom_attributes[attribute] = ge_user[attribute]
                custom_attribute = CustomAttributeUserStorage(
                    name=attribute, value=ge_user[attribute])
                custom_attributes.append(custom_attribute)
        return custom_attributes
