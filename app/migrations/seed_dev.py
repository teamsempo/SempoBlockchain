import sys
import os
import random
from uuid import uuid4
from flask import g

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..", "..")))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))

import config

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


def load_account(address, amount_wei):
    from web3 import (
        Web3,
        HTTPProvider
    )

    w3 = Web3(HTTPProvider(config.ETH_HTTP_PROVIDER))

    tx_hash = w3.eth.sendTransaction(
        {'to': address, 'from': w3.eth.accounts[0], 'value': amount_wei})
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
            fund_amount_wei=0
        )

        reserve_token = Token(address=reserve_token_address, name=name, symbol=symbol)
        reserve_token.decimals = 18

        db.session.add(reserve_token)

        return reserve_token


def get_or_create_organisation(name, org_token):
    return _get_or_create_model_object(Organisation, {'name': name}, token=org_token)


def get_or_create_admin_user(email, admin_organisation):
    instance = User.query.filter_by(
        email=str(email).lower()).first()
    if instance:
        return instance
    else:
        user = User()
        user.create_admin_auth(
            email=email,
            password='TestPassword',
            tier='sempoadmin',
            organisation=admin_organisation
        )

        user.is_activated = True
        db.session.add(user)

        return user


def get_or_create_transfer_usage(name):
    return _get_or_create_model_object(TransferUsage, {'name': name})


def get_or_create_transfer_user(email, business_usage):
    instance = User.query.filter_by(
        email=str(email).lower()).first()
    if instance:
        return instance
    else:
        instance = User(email=email, business_usage=business_usage)

        db.session.add(instance)
        return instance


def get_or_create_transer_account(name, organisation):
    return _get_or_create_model_object(
        TransferAccount, {'name': name}, organisation=organisation)


def create_users_different_transer_usage(wanted_nr_users, new_organisation):
    i = 1
    user_list = []
    transer_usages = TransferUsage.query.all()
    while i < wanted_nr_users:
        random_usage = random.choice(transer_usages)
        new_user = get_or_create_transfer_user(
            f'user-nr-{i}@test.com', random_usage)
        new_transer_account = get_or_create_transer_account(
            'transfer-account-nr-' + str(i), new_organisation)

        if len(new_user.transfer_accounts) < 1:
            new_user.transfer_accounts.append(new_transer_account)
        user_list.append(new_user)
        i += 1
    return user_list


def create_transfer(amount, sender_user, recipient_user, token):
    transfer = CreditTransfer(
        amount=amount,
        sender_user=sender_user,
        recipient_user=recipient_user,
        token=token,
        uuid=str(uuid4()))
    db.session.add(transfer)
    transfer.resolve_as_completed()

    return transfer


def create_transfers(user_list, wanted_nr_transfers, token):
    transfer_list = []
    i = 0
    while i < wanted_nr_transfers:
        try:
            shuffled = user_list.copy()
            random.shuffle(shuffled)

            transfer = create_transfer(
                amount=random.randint(1, 5),
                sender_user=shuffled[0],
                recipient_user=shuffled[1],
                token=token
            )

            transfer_list.append(transfer)
            i += 1
        except:
            pass
    return transfer_list


def _get_or_create_model_object(obj_class: db.Model, filter_kwargs: dict, **kwargs):

    instance = obj_class.query.filter_by(**filter_kwargs).first()

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

    # To simplify creation, we set the flask context to show all model data
    g.show_all = True

    print('Creating reserve token')
    master_address = bt.create_blockchain_wallet(private_key=config.MASTER_WALLET_PRIVATE_KEY)

    load_account(master_address, int(1e18))
    token = get_or_create_reserve_token(master_address, 'AUD Token', 'AUD')

    print('Creating organisation')
    new_organisation = get_or_create_organisation('org1', token)
    load_account(new_organisation.system_blockchain_address, int(1e18))

    print('Creating admin user')
    amount_to_load = 400
    admin_user = get_or_create_admin_user('admin@sempo.ai', new_organisation)
    admin_transfer_account = admin_user.transfer_account
    load_account(admin_transfer_account.blockchain_address, int(5e18))
    send_eth_task = bt.send_eth(
        signing_address=admin_transfer_account.blockchain_address,
        recipient_address=token.address,
        amount_wei=amount_to_load * int(1e16))

    bt.await_task_success(send_eth_task)

    admin_user.transfer_account.balance = amount_to_load

    print('Creating Transfer Usage')
    usages = list(map(
        get_or_create_transfer_usage,
        ['Broken Pencils',
         'Off Milk',
         'Stuxnet',
         'Used Playing Cards',
         '09 F9',
         'Junk Mail',
         'Cutlery',
         'Leaked Private Keys',
         'Parking Infringements',
         'Betamax Movies',
         'Hyperallergenic Soap',
         'Dioxygen Difluoride',
         'Hunter2'
         ]))

    print('Create a list of users with a different business usage id ')
    user_list = create_users_different_transer_usage(15, new_organisation)

    print('Disbursing to users')
    for user in user_list:
        create_transfer(
            amount=20,
            sender_user=admin_user,
            recipient_user=user,
            token=token
        )

    number_of_transfers = 30
    print('Creating %d transactions' % number_of_transfers)
    create_transfers(user_list, number_of_transfers, token)

    db.session.commit()
    ctx.pop()


if __name__ == '__main__':
    run_setup()
