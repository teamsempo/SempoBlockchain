import MySQLdb
import secrets as SECRETS
import pprint
from sqlalchemy import create_engine

from server.models.user import User
from server.models.transfer_usage import TransferUsage
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
        self.get_new_users_from_GE(list_of_phones)
        self.update_users_refered_by(self)

    def get_phones_from_sempo(self):
        result = users = User.query.filter(User.phone.isnot(None)).with_entities(User.phone).execution_options(
                show_all=True).all()
        return [r[0] for r in result]

    def get_new_users_from_GE(self, list_of_phones):
        print('Getting new users from GE')
        with self.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            format_strings = ','.join(['%s'] * len(list_of_phones))
            cmd = """SELECT * FROM users
                INNER JOIN community_tokens ON users.community_token_id=community_tokens.id
                INNER JOIN business_categories ON users.business_category_id=business_categories.id
                WHERE phone NOT IN (%s) LIMIT 1
            """
            cursor.execute(cmd % format_strings, tuple(list_of_phones))
            users = cursor.fetchall()
            i = 0
            print('Fetched {} users'.format(len(users)))
            for user in users:
                pprint.pprint(user)
                i += 1
                print('Adding user {} of {}. User name = {} {}'.format(i, len(users), user['first_name'], user['name']))
                self.insert_user(user)


    def insert_user(self, ge_user):
        is_beneficiary = ge_user['admin_id'] is None   # Is this the correct way to find this out?
        transfer_usage = TransferUsage.find_or_create(ge_user['business_type'])
        phone_number = None if 'DELETED' in ge_user['phone'] else ge_user['phone']
        print(phone_number)

        sempo_user = create_transfer_account_user(
            blockchain_address=ge_user['wallet_address'],
            first_name=ge_user['first_name'],
            last_name=ge_user['last_name'],
            phone=phone_number,
            preferred_language=ge_user['preferred_language'],
            is_beneficiary=is_beneficiary,
            is_vendor=not is_beneficiary,
            location=ge_user['location'],
            business_usage_id=transfer_usage.id
        )

        sempo_user.custom_attributes = self.get_custom_attributes(ge_user)
        sempo_user.is_activated = ge_user['status'] == 'Active'  # Is this the correct way to find this out?
        sempo_user.is_disabled = False
        sempo_user.is_phone_verified = True
        sempo_user.is_self_sign_up = False
        sempo_user.terms_accepted = False
        sempo_user.created = ge_user['created_at']

        sempo_user = self.add_migrated_from_ge_attribute(sempo_user)
        print('Succesfully inserted {}'.format(sempo_user.first_name))
        db.session.commit()

    def get_custom_attributes(self, ge_user):
        wanted_custom_attributes = [
            'bio',
            'gender',
            'market_enabled',
            'phone_listed',
            'national_id_number'
            ]
        custom_attributes = []
        for attribute in wanted_custom_attributes:
            if attribute in ge_user:
                custom_attribute = CustomAttributeUserStorage(
                    name=attribute, value=ge_user[attribute])
                custom_attributes.append(custom_attribute)
        return custom_attributes

    def add_migrated_from_ge_attribute(self, sempo_user):
        migrated_attribute = CustomAttributeUserStorage(
                    name='GE', value=True)
        sempo_user.custom_attributes.append(migrated_attribute)
        return sempo_user

    def update_users_refered_by(self):
        print('update_users_refered_by')
        sql = '''SELECT u1.id,
            u1."_phone",
            u1.first_name,
            u1.last_name,
            c1.id,
            c1.value
        FROM "user" u1
        INNER JOIN custom_attribute_user_storage c1 ON u1.id = c1.user_id
        WHERE c1."name" = 'GE_id'
        AND u1.id NOT IN
            (SELECT u2.id
            FROM "user" u2
            INNER JOIN custom_attribute_user_storage c2 ON u2.id = c2.user_id
            WHERE c2."name" = 'referred_by_id')
        '''
        result = db.session.execute(sql)
        users_not_refered_by_id = [row[0] for row in result]
        
    def set_referred_by(self, sempo_user, referred_by_id):
        print('set_referred_by ', referred_by_id)
        with self.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cmd = """SELECT * FROM users
                WHERE id = %s
            """
            cursor.execute(cmd, (referred_by_id,))
            refering_user_ge = cursor.fetchone()

            if 'DELETED' not in refering_user_ge['phone']:

                refering_user_sempo = User.query.filter_by(phone=refering_user_ge['phone']).execution_options(
                    show_all=True).one()

                print(refering_user_sempo)
                
                migrated_attribute = CustomAttributeUserStorage(
                        name='referred_by_id', value=refering_user_sempo.id)

                sempo_user.custom_attributes.append(migrated_attribute)
            return sempo_user

        
