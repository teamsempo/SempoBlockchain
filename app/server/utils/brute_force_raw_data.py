# This is like raw_data.py, but instead of using the existing models
# it just ham-fistedly shoves a bunch of raw data into the database
# This is meant to rapidly generate a very large dataset. 
# A baseline mock_data run is required first, to create organisations
# and tokens
import sys
import os
import random
import json
import base64

from uuid import uuid4

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from server.utils.mock_data import ADJECTIVES, ANIMALS, LOCATIONS
from server.models.user import User
from server.models.transfer_account import TransferAccount
from server.models.transfer_usage import TransferUsage
from server.models.credit_transfer import CreditTransfer

from cryptography.fernet import Fernet

from flask import g
from server import create_app, db
from eth_utils import keccak
from eth_keys import keys
from web3 import Web3
from sqlalchemy.sql import text
import datetime
from eth_keys import keys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool

import config


engine = create_engine(
    config.ETH_DATABASE_URI,
    poolclass=NullPool,
    connect_args={'connect_timeout': 5},
    pool_pre_ping=True,
    echo=False,
    echo_pool=False,
)
session_factory = sessionmaker(autocommit=False, autoflush=True, bind=engine)
eth_worker_session = scoped_session(session_factory)


def refresh_all_balances():
    all_accounts = db.session.query(TransferAccount).all()
    for ta in all_accounts:
        ta.update_balance()

def encrypt_private_key(private_key):
    private_key_bytes = _bytify_if_required(private_key)
    return _cipher_suite()\
        .encrypt(private_key_bytes).decode('utf-8')

def _bytify_if_required(string):
    return string if isinstance(string, bytes) else string.encode('utf-8')

def _cipher_suite():
    fernet_encryption_key = base64.b64encode(keccak(text=config.SECRET_KEY))
    return Fernet(fernet_encryption_key)

def address_from_private_key(private_key):
    if isinstance(private_key, str):
        private_key = bytes.fromhex(private_key.replace('0x', ''))
    return keys.PrivateKey(private_key).public_key.to_checksum_address()


def get_max_user_id():
    return db.session.query(db.func.max(User.id)).first()[0]

def get_max_transfer_account_id():
    return db.session.query(db.func.max(TransferAccount.id)).first()[0]

def get_max_credit_transfer_id():
    return db.session.query(db.func.max(CreditTransfer.id)).first()[0]

def get_transfer_usage_ids():
    usages = db.session.query(TransferUsage).all()
    return [usage.id for usage in usages]

def refresh_indices():
    statement = text("""SELECT pg_catalog.setval(pg_get_serial_sequence('credit_transfer', 'id'), MAX(id)) FROM credit_transfer;""")
    db.session.execute(statement)
    statement = text("""SELECT pg_catalog.setval(pg_get_serial_sequence('transfer_account', 'id'), MAX(id)) FROM transfer_account;""")
    db.session.execute(statement)
    statement = text("""SELECT pg_catalog.setval(pg_get_serial_sequence('user', 'id'), MAX(id)) FROM "user";""")
    db.session.execute(statement)
    statement = text("""SELECT pg_catalog.setval(pg_get_serial_sequence('blockchain_wallet', 'id'), MAX(id)) FROM "blockchain_wallet";""")
    eth_worker_session.execute(statement)


def create_random_user_data(id, starting_balance=2e19):
    first_name, middle_name = random.sample(ADJECTIVES, 2)
    last_name = f'{middle_name} {random.choice(ANIMALS)}'
    location, lat, lng = random.choice(LOCATIONS)

    phone = '+1' + ''.join([str(random.randint(0,10)) for i in range(0, 10)])
    attribute_dict = {'custom_attributes': {}}
    attribute_dict['custom_attributes']['gender'] = random.choice(['male', 'female'])
    address = Web3.toHex(keccak(os.urandom(4096)))

    pk = keccak(os.urandom(4096))
    address = keys.PrivateKey(pk).public_key.to_checksum_address()
    encrypted_private_key = encrypt_private_key(pk)

    phone = '+1' + ''.join([str(random.randint(0,10)) for i in range(0, 10)])
    email = first_name+'_'+str(random.randint(1, 100000))+'_'+middle_name+'@example.com'
    one_year_ago = (datetime.datetime.today() - datetime.timedelta(days=366)).strftime('%Y-%m-%d')
    user = {
        'id': id,
        'created': one_year_ago,
        'email': email, 
        'password_hash': 'gAAAAABfdnMEzfistGZkiJrd2NsP5oMscIpdlswNawM7muyoqOcXIR1ROoyG6jIhXlnR0kLtmoAEhduvEjBukgLoukcGKInmjTaOomaaw_C0wu49smPCBzo48i5X-qKqheqPNXEBWxtvx-gbs81Q_5D9FcAB4ZY_Ew==',
        'is_activated': False,
        '_phone': phone,
        'one_time_code': 0000,
        'secret': 'LI1Udfg0aIbWiq81',
        'first_name': first_name,
        'last_name': last_name,
        'terms_accepted': True,
        'is_disabled': False,
        '_location': location,
        'lat': lat,
        'lng': lng,
        'TFA_enabled': False,
        'is_phone_verified': False,
        '_held_roles': json.dumps({"BENEFICIARY": "beneficiary"}),
        'default_organisation_id': 1, # Default to Org 1, can change later
        'is_self_sign_up': False,
        'default_transfer_account_id': id,
        'is_public': False,
        'primary_blockchain_address':address,
        'failed_pin_attempts': 0,
        'pin_reset_tokens': json.dumps([]),
        'seen_latest_terms': False,
        'is_market_enabled': False
    }

    transfer_account = {
        'id': id,
        'created': one_year_ago,
        'is_approved': False,
        'is_vendor': False,
        'payable_period_length': 2,
        'payable_period_type': 'week',
        'payable_epoch': one_year_ago,
        'is_beneficiary': 't',
        'updated': one_year_ago,
        'organisation_id': 1,
        'token_id': 1,
        'blockchain_address': address,
        'account_type': 'USER',
        '_balance_wei': starting_balance,
        'is_public': False,
        'is_ghost': False,
        '_balance_offset_wei': 0,
    }

    blockchain_wallet = {
        'id': id,
        'created': one_year_ago,
        'updated': one_year_ago,
        'address': address,
        '_encrypted_private_key': encrypted_private_key,
        'wei_topup_threshold': 10000000000000000,
        'wei_target_balance': 10000000000000000,
    }

    return user, transfer_account, blockchain_wallet

def insert_user(id, user_dict, transfer_account_dict, blockchain_wallet_dict):
    statement = text("""INSERT INTO "transfer_account" (
        id,
        created,
        is_approved,
        is_vendor,
        payable_period_length,
        payable_period_type,
        payable_epoch,
        is_beneficiary,
        updated,
        organisation_id,
        token_id,
        blockchain_address,
        account_type,
        _balance_wei,
        is_public,
        is_ghost,
        _balance_offset_wei
    ) VALUES(
        :id,
        :created,
        :is_approved,
        :is_vendor,
        :payable_period_length,
        :payable_period_type,
        :payable_epoch,
        :is_beneficiary,
        :updated,
        :organisation_id,
        :token_id,
        :blockchain_address,
        :account_type,
        :_balance_wei,
        :is_public,
        :is_ghost,
        :_balance_offset_wei
    )""")
    db.session.execute(statement, transfer_account_dict)


    statement = text("""INSERT INTO "user" (
        id,
        created,
        email,
        password_hash,
        is_activated,
        _phone,
        one_time_code,
        secret,
        first_name,
        last_name,
        terms_accepted,
        is_disabled,
        _location,
        lat,
        lng,
        is_phone_verified,
        _held_roles,
        default_organisation_id,
        is_self_sign_up,
        default_transfer_account_id,
        is_public,
        primary_blockchain_address,
        failed_pin_attempts,
        pin_reset_tokens,
        seen_latest_terms,
        is_market_enabled
    ) VALUES(
        :id,
        :created,
        :email,
        :password_hash,
        :is_activated,
        :_phone,
        :one_time_code,
        :secret,
        :first_name,
        :last_name,
        :terms_accepted,
        :is_disabled,
        :_location,
        :lat,
        :lng,
        :is_phone_verified,
        :_held_roles,
        :default_organisation_id,
        :is_self_sign_up,
        :default_transfer_account_id,
        :is_public,
        :primary_blockchain_address,
        :failed_pin_attempts,
        :pin_reset_tokens,
        :seen_latest_terms,
        :is_market_enabled
    )""")
    db.session.execute(statement, user_dict)

    statement = text("""INSERT INTO organisation_association_table (
        organisation_id,
        user_id
    ) VALUES(
        :org_id,
        :user_id
    )""")
    db.session.execute(statement, {'org_id': 1, 'user_id': id})
    
    statement = text("""INSERT INTO organisation_association_table (
        organisation_id,
        transfer_account_id
    ) VALUES(
        :org_id,
        :transfer_account_id
    )""")
    db.session.execute(statement, {'org_id': 1, 'transfer_account_id': id})


    statement = text("""INSERT INTO user_transfer_account_association_table (
        user_id,
        transfer_account_id
    ) VALUES(
        :user_id,
        :transfer_account_id
    )""")
    db.session.execute(statement, {'user_id': id, 'transfer_account_id': id})

    statement = text("""INSERT INTO "blockchain_wallet" (
        created,
        updated,
        address,
        _encrypted_private_key,
        wei_topup_threshold,
        wei_target_balance
    ) VALUES(
        :created,
        :updated,
        :address,
        :_encrypted_private_key,
        :wei_topup_threshold,
        :wei_target_balance
    )""")
    eth_worker_session.execute(statement, blockchain_wallet_dict)



def generate_user_transactions(sender_id, min_recipient_id, max_recipient_id, base_transaction_id, usages, number_of_transactions=10, max_transaction_amount=2e18):
    for n in range(number_of_transactions):
        id = base_transaction_id + n
        print(id)
        created = (datetime.datetime.now() - datetime.timedelta(hours=random.randrange(1,2080))).strftime("%m/%d/%Y, %H:%M:%S") # Random hour in past year
        recipient_id = random.randrange(min_recipient_id, max_recipient_id)
        transaction_amount = random.randrange(1, max_transaction_amount)
        transaction = {
            'id': id, 
            'created': created,
            'resolved_date': created,
            'transfer_type': 'PAYMENT',
            'transfer_mode': random.choice(['NFC', 'USSD', 'SMS', 'QR']),
            'transfer_status': 'COMPLETE',
            'sender_transfer_account_id': sender_id,
            'recipient_transfer_account_id': recipient_id,
            'recipient_user_id': recipient_id,
            'sender_user_id': sender_id,
            'updated': created,
            'uuid': str(uuid4()),
            'token_id': 1,
            'transfer_subtype': 'STANDARD',
            '_transfer_amount_wei': transaction_amount,
            'is_public': False,
            'blockchain_task_uuid': str(uuid4()),
            'exclude_from_limit_calcs': False,
            'blockchain_hash': str(uuid4()),
            'blockchain_status': 'SUCCESS',
            'last_worker_update': created
        }
    
        statement = text("""INSERT INTO credit_transfer (
            id,
            created,
            resolved_date,
            transfer_type,
            transfer_mode,
            transfer_status,
            sender_transfer_account_id,
            recipient_transfer_account_id,
            recipient_user_id,
            sender_user_id,
            updated,
            uuid,
            token_id,
            transfer_subtype,
            _transfer_amount_wei,
            is_public,
            blockchain_task_uuid,
            exclude_from_limit_calcs,
            blockchain_hash,
            blockchain_status,
            last_worker_update
            ) VALUES(
            :id,
            :created,
            :resolved_date,
            :transfer_type,
            :transfer_mode,
            :transfer_status,
            :sender_transfer_account_id,
            :recipient_transfer_account_id,
            :recipient_user_id,
            :sender_user_id,
            :updated,
            :uuid,
            :token_id,
            :transfer_subtype,
            :_transfer_amount_wei,
            :is_public,
            :blockchain_task_uuid,
            :exclude_from_limit_calcs,
            :blockchain_hash,
            :blockchain_status,
            :last_worker_update
        )""")
        db.session.execute(statement, transaction)

        statement = text("""INSERT INTO credit_transfer_transfer_usage_association_table (
            credit_transfer_id,
            transfer_usage_id
        ) VALUES(
            :credit_transfer_id,
            :transfer_usage_id
        )""")
        db.session.execute(statement, {'credit_transfer_id': id, 'transfer_usage_id': random.choice(usages)})


        statement = text("""INSERT INTO organisation_association_table (
            organisation_id,
            credit_transfer_id
        ) VALUES(
            :organisation_id,
            :credit_transfer_id
        )""")
        db.session.execute(statement, {'organisation_id': 1, 'credit_transfer_id': id})
    return id    

if __name__ == '__main__':

    app = create_app()
    ctx = app.app_context()
    ctx.push()
    g.show_all = True
    refresh_indices()
 
    print('Generating Users and Accounts')
    accounts_to_make = 10
    max_user_id = get_max_user_id()
    max_transfer_account_id = get_max_transfer_account_id() 
    base_id = max(max_user_id, max_transfer_account_id)

    for i in range(1, accounts_to_make + 1):
        account_id = base_id + i
        if(i %10 == 0):
            print(f'Making transfer account {i} of {accounts_to_make} - {(i/accounts_to_make)*100}%')
            db.session.commit()
        # We'll be generating our own IDs, so we start at maximum to avoid overlap
        # Just using max of user and transfer account since them having matching IDs is just easier
        user, transfer_account, blockchain_wallet = create_random_user_data(account_id)
        insert_user(account_id, user, transfer_account, blockchain_wallet)
    refresh_indices()
    db.session.commit()
    
    base_transaction_id = get_max_credit_transfer_id() + 1
    usages = get_transfer_usage_ids()
    for i in range(base_id, base_id+accounts_to_make):
        base_transaction_id = generate_user_transactions(i, base_id, base_id + accounts_to_make, base_transaction_id, usages) + 1
    
    statement = text("""SELECT pg_catalog.setval(pg_get_serial_sequence('credit_transfer', 'id'), MAX(id)) FROM credit_transfer;""")
    refresh_indices()
    db.session.commit()
    refresh_all_balances()




#  # Add blockchain_task
#   id  |          created           |          updated           |       function       |                                                                           args                                                                            | kwargs | is_send_eth |             recipient_address              | gas_limit | signing_wallet_id |     abi_type     |      _type      |              contract_address              |      contract_name       |         _amount          |                 uuid                 | status_text | previous_invocations | reverses_id
#   167 | 2020-10-05 16:59:02.123086 | 2020-10-05 16:59:02.438805 | transfer             | ["0xF5a42843b940f622B1614069E023b12B632F8087", 1000000000000000000]                                                                                       | null   | f           |                                            |           |                 1 | ERC20            | FUNCTION        | 0xbc1A4f5A7c8FBA171A8F4db85FF1F28cF0a0590f |                          |                          | e360c613-dc35-4677-acee-f1e679e63219 | SUCCESS     |                    0 |
#  # Add blockchain_transaction
#   id  |          created           |          updated           | _status |     error     | message | block |       submitted_date       |         mined_date         |                                hash                                | nonce | nonce_consumed | blockchain_task_id | signing_wallet_id | ignore |              contract_address              |                          first_block_hash                          | is_synchronized_with_app | amount | recipient_address | sender_address | is_third_party_transaction
#   142 | 2020-10-05 16:59:02.181683 | 2020-10-05 16:59:02.424106 | SUCCESS |               |         |   139 | 2020-10-05 16:59:02.329967 | 2020-10-05 16:59:02.391868 | 0xc75aa32d20d342f9af679d8526491d7a799d86dae52f6fd1d50758eea1180dec |   115 | t              |                167 |                 1 | f      |                                            | 0x68002ba7197d6910b4166859c9cf77513b1dc6926be7121d41e432936017e95a | t                        |        |                   |                | f
#  
#  # Add blockchain_wallet
#   id |          created           |          updated           |                  address                   |                                                                                  _encrypted_private_key                                                                                  | wei_topup_threshold | wei_target_balance  |         last_topup_task_uuid
#   21 | 2020-10-05 16:40:07.923703 | 2020-10-05 16:40:07.96185  | 0x565f45bA87d24ED0c36293b5b426484A6194461e | gAAAAABfe0xnejhsUMvTBUS_P1ltvUxD1l_PWXudyCqg9nPfqrevJ9QWN7LtUs7A5mKZqF0N4HHUTjIb_vV5AcwkP4xeXPjRcoKZfOh-6-ROmrFIN9iUyPc_RToq7DNTxQJFnFVPmjx8KjaVblk9qyQ1kYlehLodQxoqx50d17nPOJdXnBZ9Nvk= |   10000000000000000 |   20000000000000000 | 445141f7-1ff4-41e5-85b4-9d25cea6238f