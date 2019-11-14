import sys
import os
import time
import random
from uuid import uuid4
import string
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..", "..")))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))

from server import create_app, db, bt
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

def load_account(address):
    from web3 import (
        Web3,
        HTTPProvider
    )
    import config

    w3 = Web3(HTTPProvider(config.ETH_HTTP_PROVIDER))

    tx_hash = w3.eth.sendTransaction(
        {'to': address, 'from': w3.eth.accounts[0], 'value': 5 * 10 ** 18})
    return w3.eth.waitForTransactionReceipt(tx_hash)


def get_or_create_reserve_token(deploying_address, name, symbol):

    reserve_token = Token.query.filter_by(symbol=symbol).first()
    if reserve_token:
        return reserve_token

    else:
        reserve_token_address = bt.deploy_and_fund_reserve_token(
            deploying_address=deploying_address,
            name=name,
            symbol=symbol,
            fund_amount_wei=4 * 10 ** 18
        )

        reserve_token = Token(address=reserve_token_address, name=name, symbol=symbol)
        reserve_token.decimals = 18

        db.session.add(reserve_token)

        return reserve_token


def get_or_create_transfer_usage(name):
    return _get_or_create_model_object(TransferUsage, {'name': name})


def get_or_create_organisation(name, org_token):
    return _get_or_create_model_object(Organisation, {'name': name}, token=org_token)


def get_or_create_admin_user(email, admin_organisation):
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

        user.organisations.append(admin_organisation)
        user.default_organisation = admin_organisation

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
    return _get_or_create_model_object(
        TransferAccount, {'name': name}, blockchain_address=blockchain_address, organisation=organisation
    )

def create_users_different_transer_usage(wanted_nr_users, blockchain_address, new_organisation):
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


def create_transfers(sender, user_list, wanted_nr_transfers, token):
    transfer_list = []
    i = 0
    while i < wanted_nr_transfers:
        transfer = CreditTransfer(
            i,
            sender_user=sender,
            recipient_user=random.choice(user_list),
            token=token,
            uuid=str(uuid4()))
        db.session.add(transfer)

        transfer.resolve_as_completed()
        transfer_list.append(transfer)
        i += 1
    return transfer_list


def _get_or_create_model_object(obj_class: db.Model, filter_kwargs: dict, **kwargs):

    instance = obj_class.query.execution_options(show_all=True).filter_by(**filter_kwargs).first()

    if instance:
        return instance
    else:
        print('Creating new obj')
        instance = obj_class(**{**filter_kwargs, **kwargs})
        db.session.add(instance)
        return instance


def run_setup():
    app = create_app()
    ctx = app.app_context()
    ctx.push()

    print('Creating token')
    blockchain_address = '0xc1275b7de8af5a38a93548eb8453a498222c4ff2'
    token = get_or_create_reserve_token(blockchain_address,
                                'AUD Token', 'AUD')

    print('Creating Transfer Usage')
    usage = get_or_create_transfer_usage('Test Usage 2')

    db.session.commit()

    print('Creating admin user')
    admin_user = get_or_create_admin_user('administrator@sempo.ai')

    print('Creating organisation')
    new_organisation = get_or_create_organisation('org1', token)

    print('Creating user 1')
    user1 = get_or_create_user('sender-user@test.com', usage.id)

    transer_account1 = get_or_create_transer_account(
        'transfer-account', blockchain_address, new_organisation)
    if len(user1.transfer_accounts) < 1:
        user1.transfer_accounts.append(transer_account1)

    print('Create a list of users with a different business usage id ')
    user_list = create_users_different_transer_usage(15, blockchain_address, new_organisation)

    number_of_transfers = 30
    print('Creating %d transactions' % number_of_transfers)
    # User 1 sends to a random choice of user_list
    create_transfers(user1, user_list, number_of_transfers, token)

    db.session.commit()
    ctx.pop()


if __name__ == '__main__':
    run_setup()
