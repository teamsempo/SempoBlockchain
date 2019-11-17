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
from server.models.exchange import ExchangeContract, Exchange
from server.models.user import User
from server.models.transfer_usage import TransferUsage


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


def create_or_get_reserve_token(
        deploying_address,
        reserve_token,
        name, symbol, reserve_ratio_ppm,
        reserve_deposit_wei,
        issue_amount_wei,
        registry_address=None,
        exchange_contract=None):

    if registry_address is None:
        registry_address = bt.deploy_exchange_network(deploying_address)

    smart_token_result = bt.deploy_smart_token(
        deploying_address=deploying_address,
        name=name, symbol=symbol, decimals=18,
        reserve_deposit_wei=reserve_deposit_wei,
        issue_amount_wei=issue_amount_wei,
        contract_registry_address=registry_address,
        reserve_token_address=reserve_token.address,
        reserve_ratio_ppm=reserve_ratio_ppm
    )


    smart_token_address = smart_token_result['smart_token_address']
    subexchange_address = smart_token_result['subexchange_address']

    smart_token = Token(address=smart_token_address, name=name, symbol=symbol)
    smart_token.decimals = 18

    db.session.add(smart_token)

    if exchange_contract is None:

        exchange_contract = ExchangeContract(
            blockchain_address=subexchange_address,
            contract_registry_blockchain_address=registry_address
        )

    exchange_contract.add_reserve_token(reserve_token)
    exchange_contract.add_token(smart_token, subexchange_address, reserve_ratio_ppm)

    return smart_token, exchange_contract, registry_address


def make_exchange(user, from_token, to_token, from_amount):
    exchange = Exchange()

    exchange.exchange_from_amount(
        user=user,
        from_token=from_token,
        to_token=to_token,
        from_amount=from_amount
    )

    db.session.add(exchange)
    db.session.commit()

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


def get_or_create_transfer_user(email, business_usage, organisation):
    user = User.query.filter_by(
        email=str(email).lower()).first()
    if user:
        return user
    else:
        user = User(email=email,
                        business_usage=business_usage,
                        default_organisation=organisation)
        db.session.add(user)

        user.organisations.append(organisation)

        transfer_account = TransferAccount(bind_to_entity=user)
        db.session.add(transfer_account)

        return user


def get_or_create_transer_account(name, user):
    return _get_or_create_model_object(
        TransferAccount, {'name': name}, bind_to_entity=user)


def seed_transfers(user_list, admin_user, token):
    print('Disbursing to users')
    for user in user_list:
        create_transfer(
            amount=50,
            sender_user=admin_user,
            recipient_user=user,
            token=token
        )

    number_of_transfers = 30
    print('Creating %d transactions' % number_of_transfers)
    create_transfers(user_list, number_of_transfers, token)


def create_users_different_transer_usage(wanted_nr_users, new_organisation):
    i = 1
    user_list = []
    transer_usages = TransferUsage.query.all()
    while i < wanted_nr_users:
        random_usage = random.choice(transer_usages)

        new_user = get_or_create_transfer_user(
            f'user-nr-{i}@test.com',
            random_usage,
            new_organisation
        )

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

    master_organisation = Organisation.query.filter_by(is_master=True).first()
    if master_organisation is None:
        print('Creating master organisation')
        master_organisation = Organisation(is_master=True)
        db.session.add(master_organisation)

    master_system_address = master_organisation.system_blockchain_address

    load_account(master_system_address, int(1e18))
    reserve_token = get_or_create_reserve_token(master_system_address, 'AUD Token', 'AUD')

    master_organisation.token = reserve_token

    print('Creating organisation')
    new_organisation = get_or_create_organisation('org1', reserve_token)
    load_account(new_organisation.system_blockchain_address, int(1e18))

    print('Creating admin user')
    amount_to_load = 1000
    admin_user = get_or_create_admin_user('admin@sempo.ai', new_organisation)
    admin_transfer_account = admin_user.transfer_account
    load_account(admin_transfer_account.blockchain_address, int(20e18))
    send_eth_task = bt.send_eth(
        signing_address=admin_transfer_account.blockchain_address,
        recipient_address=reserve_token.address,
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

    print('Making Bulk Transfers')
    seed_transfers(user_list, admin_user, reserve_token)

    print('Deploying Smart Token')
    smart_token, exchange_contract, registry_address = create_or_get_reserve_token(
        deploying_address=admin_transfer_account.blockchain_address,
        reserve_token=reserve_token,
        reserve_deposit_wei=5e17,
        issue_amount_wei=5e17,
        name='CIC1', symbol='CIC1', reserve_ratio_ppm=250000
    )

    print('Making exchanges')
    make_exchange(
        user=admin_user,
        from_token=reserve_token,
        to_token=smart_token,
        from_amount=2
    )

    create_transfer(
        amount=10,
        sender_user=admin_user,
        recipient_user=user_list[0],
        token=reserve_token
    )

    make_exchange(
        user=user_list[0],
        from_token=reserve_token,
        to_token=smart_token,
        from_amount=10
    )

    create_transfer(
        amount=2,
        sender_user=user_list[0],
        recipient_user=user_list[1],
        token=smart_token
    )

    db.session.commit()
    ctx.pop()


if __name__ == '__main__':
    run_setup()
