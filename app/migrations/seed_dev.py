import sys
import os
import time
import random
from uuid import uuid4
import string
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..", "..")))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))

from server import db, create_app
from server.models.token import Token
from server.models.organisation import Organisation
from server.models.credit_transfer import CreditTransfer
from server.models.transfer_account import TransferAccount
from server.models.blockchain_address import BlockchainAddress
from server.models.user import User
from server.models.transfer_usage import TransferUsage
from server.models.ussd import UssdMenu
from server.utils import user as UserUtils
from server.utils.transfer_enums import TransferStatusEnum

def get_or_create_token(address, name, symbol):
    instance = Token.query.filter_by(address=address).first()
    print(instance)
    if instance:
        return instance
    else:
        instance = Token(address=address,
                         name=name,
                         symbol=symbol)

        db.session.add(instance)
        return instance


def get_or_create_organisation(name, token):
    instance = Organisation.query.filter_by(name=name).first()
    print(instance)
    if instance:
        return instance
    else:
        instance = Organisation(name=name, token=token)

        db.session.add(instance)   
        return instance


def get_or_create_admin_user(email):
    instance = User.query.execution_options(show_all=True).filter_by(
        email=str(email).lower()).first()
    if instance:
        return instance
    else:
        user = User()
        user.create_admin_auth(email=email,
                               password='TestPassword', tier='sempoadmin')

        user.is_activated = True
        db.session.add(user)
        return user
   

def get_or_create_user(email, business_usage_id):
    instance = User.query.execution_options(show_all=True).filter_by(
        email=str(email).lower()).first()
    if instance:
        return instance
    else:
        instance = User(email=email, business_usage_id=business_usage_id)

        db.session.add(instance)
        return instance


def get_or_create_transer_account(name, blockchain_address, organisation):
    instance = TransferAccount.query.filter_by(name=name).first()
    if instance:
        return instance
    else:
        instance = TransferAccount(
            blockchain_address=blockchain_address, organisation=organisation)

        instance.name = name
        db.session.add(instance)
        return instance


def create_users_different_transer_usage(wanted_nr_users):
    i = 1
    user_list = []
    transer_usages_ids = TransferUsage.query.with_entities(
        TransferUsage.id).all()
    while i < wanted_nr_users:
        random_usage_id = random.choice(transer_usages_ids)[0]
        new_user = get_or_create_user(
            'user-nr-' + str(i) + '@test.com', random_usage_id)
        new_transer_account = get_or_create_transer_account(
            'transfer-account-nr-' + str(i), blockchain_address, new_organisation)

        if len(new_user.transfer_accounts) < 1:
            new_user.transfer_accounts.append(new_transer_account)
        user_list.append(new_user)
        i += 1
    return user_list


def create_transfers(sender, user_list, wanted_nr_transfers):
    transfer_list = []
    i = 0
    while i < wanted_nr_transfers:
        transfer = CreditTransfer(
                                    i,
                                    sender_user=sender,
                                    recipient_user=random.choice(user_list),
                                    token=token,
                                    uuid=str(uuid4()))
        transfer.transfer_status = TransferStatusEnum.COMPLETE
        db.session.add(transfer)
        transfer_list.append(transfer)
        i += 1
    return transfer_list


if __name__ == '__main__':

    app = create_app()
    ctx = app.app_context()
    ctx.push()

    print('Creating admin user')
    admin_user = get_or_create_admin_user('administrator@sempo.ai')

    print('Creating token')
    blockchain_address = '0xc1275b7de8af5a38a93548eb8453a498222c4ff2'
    token = get_or_create_token(blockchain_address,
                                'AUD Token', 'AUD')

    db.session.commit()

    print('Creating organisation')
    new_organisation = get_or_create_organisation('org1', token)

    print('Creating user 1')
    user1 = get_or_create_user('sender-user@test.com', 1)
    transer_account1 = get_or_create_transer_account(
        'transfer-account', blockchain_address, new_organisation)
    if len(user1.transfer_accounts) < 1:
        user1.transfer_accounts.append(transer_account1)

    print('Create a list of users with a different business usage id ')
    user_list = create_users_different_transer_usage(15)

    number_of_transfers = 30
    print('Creating %d transactions' % number_of_transfers)
    # User 1 sends to a random choice of user_list
    create_transfers(user1, user_list, number_of_transfers)

    db.session.commit()
    ctx.pop()
