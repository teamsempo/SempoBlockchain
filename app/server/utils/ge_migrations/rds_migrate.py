from flask import current_app
import MySQLdb
import time
from sqlalchemy.exc import IntegrityError, InvalidRequestError
import pprint

from server import db, bt

from server.models.user import User
from server.models.organisation import Organisation
from server.models.transfer_usage import TransferUsage
from server.models.token import Token
from server.models.kyc_application import KycApplication
from server.models.credit_transfer import CreditTransfer
from server.utils.user import create_transfer_account_user
from server.utils.phone import proccess_phone_number
from server.models.custom_attribute_user_storage import CustomAttributeUserStorage
from server.utils.ge_migrations.poa_explorer import POAExplorer
from server.utils.ge_migrations.web3_explorer import get_token_balance
from server.utils.transfer_enums import TransferTypeEnum, TransferSubTypeEnum
from server.constants import GE_MIGRATION_TOKENS

class RDSMigrate:
    
    '''
    Access to a MySQL relational database in AWS. This class will be
    used to migrate the 2 databases
    '''

    def __init__(self, sempo_organisation_id, ge_community_token_id=None, user_limit=10000):
        self.poa = POAExplorer()
        timeout = 120
        print('RDSMigrate: Creating a connection, with a %d sec timeout.' % timeout)
        self.connection = MySQLdb.connect(host=current_app.config['GE_DB_HOST'],
                                          db=current_app.config['GE_DB_NAME'],
                                          user=current_app.config['GE_DB_USER'],
                                          port=int(current_app.config['GE_DB_PORT']),
                                          password=current_app.config['GE_DB_PASSWORD'],
                                          connect_timeout=timeout)

        if not self.connection:
            raise RuntimeError('Could not connect to database')
        else:
            print('DB connection successfully created.  Yeah us.')

        self.sempo_organisation_id = sempo_organisation_id
        self.ge_community_token_id = ge_community_token_id
        self.user_limit = user_limit

    def migrate(self):
        self.migrateUsers()

        # self.migratePOA()

        print('Migration Complete!')

    def migrateUsers(self):
        list_of_ge_ids = self.get_ids_from_sempo()
        # print('list_of_ge_ids', list_of_ge_ids)
        self.get_new_users_from_GE(list_of_ge_ids, community_token_id=self.ge_community_token_id)
        # self.update_users_refered_by()

    def get_ids_from_sempo(self):
        sql = '''SELECT
            c1.value::text::int
            FROM "user" u1
            INNER JOIN custom_attribute_user_storage c1 ON u1.id = c1.user_id
            WHERE c1."name" = 'GE_id'
        '''
        result = db.session.execute(sql)
        list_of_ids = [r[0] for r in result]
        if len(list_of_ids) > 0:
            return list_of_ids
        else:
            return [0]


    def get_new_users_from_GE(self,
                              already_added_ge_ids: list,
                              community_token_id: int = None):

        print('Getting new users from GE')
        with self.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            format_strings = ','.join(['%s'] * len(already_added_ge_ids))
            cmd = f"""SELECT * FROM users
                LEFT JOIN community_tokens ON users.community_token_id=community_tokens.id
                LEFT JOIN business_categories ON users.business_category_id=business_categories.id
                LEFT JOIN token_agents on users.id=token_agents.user_id
                LEFT JOIN group_accounts on users.id=group_accounts.user_id
                WHERE users.id NOT IN (%s)
                LIMIT {self.user_limit}
            """

            if community_token_id:
                cmd = cmd + f" AND users.community_token_id={community_token_id}"

            cursor.execute(cmd % format_strings, tuple(already_added_ge_ids))
            users = cursor.fetchall()
            i = 0
            print('Fetched {} users'.format(len(users)))

            n_users = len(users)
            t0 = time.time()
            estimate_time_left = 'unknown'

            ge_address_to_user = {}
            for user in users:
                i += 1               
                print('Adding user {} of {}. User name = {} {}. Estimated time left {}. seconds'.format(
                        i, n_users, user['first_name'], user['name'], estimate_time_left))
                # pprint.pprint(user)
                sempo_user = self.insert_user(user)

                if sempo_user:
                    ge_address_to_user[user['wallet_address']] = sempo_user

                    self.migrate_balances({user['wallet_address']: sempo_user})

                    db.session.commit()

                elapsed_time = time.time() - t0
                estimate_time_left = round((elapsed_time / i * n_users) - elapsed_time, 1)


            # self.migrate_balances(ge_address_to_user)


    def insert_user(self, ge_user):

        phone_number = None if 'DELETED' in ge_user['phone'] else ge_user['phone']

        if not phone_number:
            return

        processed_phone = proccess_phone_number(phone_number)
        existing_user = User.query.filter_by(phone=processed_phone).execution_options(show_all=True).first()
        if existing_user:
            print(f'User already exists for phone {processed_phone}')
            return

        if ge_user['admin_id']:
            return

        if ge_user['business_type'] is not None:
            transfer_usage = TransferUsage.find_or_create(ge_user['business_type'])
            business_usage_id = transfer_usage.id
        else:
            business_usage_id = None

        if business_usage_id:
            business_usage = TransferUsage.query.get(business_usage_id)
        else:
            business_usage = None

        organsation = db.session.query(Organisation).get(self.sempo_organisation_id)

        try:
            sempo_user = create_transfer_account_user(
                first_name=ge_user['first_name'],
                last_name=ge_user['last_name'],
                organisation=organsation,
                phone=phone_number,
                preferred_language=ge_user['preferred_language'],
                location=ge_user['location'],
                business_usage=business_usage
            )

            sempo_user.pin_hash = ge_user['encrypted_pin']
            sempo_user.is_activated = ge_user['status'] == 'Active'  # Is this the correct way to find this out?
            sempo_user.is_disabled = False
            sempo_user.is_phone_verified = True
            sempo_user.is_self_sign_up = False
            sempo_user.terms_accepted = False
            sempo_user.created = ge_user['created_at']
            sempo_user.custom_attributes = self.create_custom_attributes(ge_user)

            if ge_user['token_agents.id'] is not None:
                sempo_user.set_held_role('TOKEN_AGENT', 'grassroots_token_agent')
            else:
                # Is this the correct way to find this out or can a benificiary also be a token agent 
                # Or is there some field where you can find this out?
                sempo_user.set_held_role('BENEFICIARY', 'beneficiary')

            if ge_user['group_accounts.id'] is not None:
                sempo_user.set_held_role('GROUP_ACCOUNT', 'grassroots_group_account')

            db.session.flush()

            return sempo_user

        except (IntegrityError, InvalidRequestError) as e:
            print(e)
            db.session().rollback()



    def create_custom_attributes(self, ge_user):

        wanted_custom_attributes = [
            ('id', 'GE_id'),
            ('wallet_address', 'GE_wallet_address'),
            ('bio', 'bio'),
            ('national_id_number', 'national_id_number'),
            ('gender', 'gender'),
            ('market_enabled', 'market_enabled'),
            ('referred_by_id', 'GE_referred_by_id'),
            ('phone_listed', 'phone_listed'),
            ('community_token_id', 'GE_community_token_id')
            ]

        custom_attributes = []
        for accessor, label in wanted_custom_attributes:
            if accessor in ge_user:
                custom_attribute = CustomAttributeUserStorage(
                    name=label, value=ge_user[accessor])
                custom_attributes.append(custom_attribute)
        return custom_attributes

    def update_users_refered_by(self):
        print('update_users_refered_by')
        ge_sempo_user_ids = self.select_users_refered_by_not_set()
        self.set_referred_by_all(ge_sempo_user_ids)

    def select_users_refered_by_not_set(self):
        sql = '''SELECT c1.value::text::int
            FROM "user" u1
            INNER JOIN custom_attribute_user_storage c1 ON u1.id = c1.user_id
            WHERE c1."name" = 'GE_id'
            AND u1.id NOT IN(
                SELECT u2.id
                FROM "user" u2
                INNER JOIN custom_attribute_user_storage c2 ON u2.id = c2.user_id
                WHERE c2."name" = 'referred_by_id'
            )
        '''
        result = db.session.execute(sql)
        users_not_refered_by_id = [row[0] for row in result]
        return users_not_refered_by_id

    def set_referred_by_all(self, ge_user_ids):
        with self.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:

            cmd = """SELECT id, referred_by_id FROM users
                WHERE id in %s AND referred_by_id IS NOT NULL;
                """
            cursor.execute(cmd, (ge_user_ids,))
            ge_id_referred_by = cursor.fetchall()
            print('ge_id_referred_by', ge_id_referred_by)

            for item in ge_id_referred_by:
                self.set_referred_by(item['id'], item['referred_by_id'])

    def set_referred_by(self, ge_id, ge_referred_by):
        sempo_referred_by = self.get_sempo_id_from_ge_id(ge_referred_by)
        if sempo_referred_by is not None:
            referred_by_attribute = CustomAttributeUserStorage(
                    name='referred_by_id', value=sempo_referred_by)

            sempo_user_id = self.get_sempo_id_from_ge_id(ge_id)
            print('sempo_user_id', sempo_user_id)
            sempo_user = User.query.filter_by(id=sempo_user_id).execution_options(
                show_all=True).one()

            sempo_user.custom_attributes.append(referred_by_attribute)

            db.session.commit()
            print('Added reference: user #{} is referenced by #{}'.format(sempo_user_id, sempo_referred_by))
        else:
            print('Referring GE user #{} not added to Sempo'.format(ge_referred_by))

    def get_sempo_id_from_ge_id(self, ge_id):
        sql = '''SELECT u1.id
                FROM "user" u1
                INNER JOIN custom_attribute_user_storage c1 ON u1.id = c1.user_id
                WHERE c1."value"::text = '{}'
        '''.format(ge_id)
        result = db.session.execute(sql.format(ge_id)).first()
        if result is not None:
            return result[0]
        else:
            return result

    def migratePOA(self):
        addresses = self.get_unmigrated_addresses()
        self.migrate_balance(addresses)
        self.migrate_transactions(addresses)

    def get_unmigrated_addresses(self):
        sql = '''SELECT t.blockchain_address
        FROM "transfer_account" t
        JOIN user_transfer_account_association_table ut on t.id = ut.transfer_account_id
        JOIN "user" u on ut.user_id = u.id
        INNER JOIN custom_attribute_user_storage c ON u.id = c.user_id
        WHERE c."name" = 'GE_id' AND t."_balance_wei" = 0
        LIMIT 2
        '''
        result = db.session.execute(sql)
        addresses = [row[0] for row in result]
        return addresses

    def migrate_balances(self, ge_address_to_user: dict):

        org = Organisation.query.get(self.sempo_organisation_id)
        token = org.token

        ge_address_to_user.pop(None, None)

        addresses = list(ge_address_to_user.keys())

        for user_address in addresses:
            balance_wei = 0

            for ge_token in GE_MIGRATION_TOKENS.keys():
                contract_address = GE_MIGRATION_TOKENS[ge_token]

                v = get_token_balance(user_address, contract_address)

                if v != '':
                    balance_wei += int(v)

            user = ge_address_to_user[user_address]
            ta = user.get_transfer_account_for_token(token)
            ta._balance_wei = balance_wei

            print(f'transfering {balance_wei} wei to {user}')

            if balance_wei != 0:

                migration_transfer = CreditTransfer(
                    amount=balance_wei/1e16,
                    token=token,
                    sender_transfer_account=org.queried_org_level_transfer_account,
                    recipient_user=user,
                    transfer_type=TransferTypeEnum.PAYMENT,
                    transfer_subtype=TransferSubTypeEnum.DISBURSEMENT
                )

                db.session.add(migration_transfer)

                migration_transfer.resolve_as_completed()

    def store_wei(self, address, balance):
        sql = '''UPDATE "transfer_account"
        SET "_balance_wei" = {}
        WHERE blockchain_address = '{}'
        '''.format(balance, address)
        db.session.execute(sql)
        db.session.commit()

    def migrate_transactions(self, addresses):
        print('migrateTransactions')
        for address in addresses:
            transactions = self.poa.transaction_list(address)
            for transaction in transactions['result']:
                self.add_transactions_sempo(transaction)

    def add_transactions_sempo(self, ge_transaction):
        pprint.pprint(ge_transaction)

        sender_user = self.get_user_from_address(ge_transaction['from'])
        recipient_user = self.get_user_from_address(ge_transaction['to'])
        token = db.session.query(Token).first()  # This should still be set to correct token
        amount = int(ge_transaction['value']) / 10 ** 16
        print('amount', amount)

        if sender_user is not None and recipient_user is not None:
            print(sender_user)
            # This is not working yet

            # transfer = CreditTransfer(
            #     amount=amount,
            #     sender_user=sender_user,
            #     recipient_user=recipient_user,
            #     token=token,
            #     uuid=str(uuid4()))

            # db.session.add(transfer)

            # transfer.resolve_as_completed()

            # transfer.transfer_type = TransferTypeEnum.PAYMENT

    def get_user_from_address(self, address):
        sql = '''SELECT u.id
        FROM "transfer_account" t
        JOIN user_transfer_account_association_table ut on t.id = ut.transfer_account_id
        JOIN "user" u on ut.user_id = u.id
        WHERE t.blockchain_address = '{}'
        '''.format(address)
        result = db.session.execute(sql).first()
        print('result', result)
        if result is not None:
            sempo_user_id = result[0]

            sempo_user = User.query.filter_by(id=sempo_user_id).execution_options(
                    show_all=True).one()
            return sempo_user
        else:
            return None
