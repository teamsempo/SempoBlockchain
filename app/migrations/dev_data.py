import sys
import os
import random
from uuid import uuid4
from flask import g

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..", "..")))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))

import config

from server import create_app, db, bt
from server.models.token import Token, TokenType
from server.models.organisation import Organisation
from server.models.credit_transfer import CreditTransfer
from server.models.transfer_account import TransferAccount
from server.models.exchange import ExchangeContract, Exchange
from server.models.user import User
from server.models.transfer_usage import TransferUsage
from server.utils.transfer_enums import TransferTypeEnum, TransferSubTypeEnum

from server.utils.user import create_transfer_account_user

data_size_options = {
    'small': {'users': 15, 'transfers': 30},
    'medium': {'users': 150, 'transfers': 300},
    'large': {'users': 1000, 'transfers': 1000}
}

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

        reserve_token = Token(address=reserve_token_address, name=name, symbol=symbol, token_type=TokenType.RESERVE)
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

    smart_token = Token(address=smart_token_address, name=name, symbol=symbol, token_type=TokenType.LIQUID)
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


def get_or_create_admin_user(email, password, admin_organisation):
    instance = User.query.filter_by(
        email=str(email).lower()).first()
    if instance:
        return instance
    else:
        user = User(first_name='Admin', last_name='user')
        user.create_admin_auth(
            email=email,
            password=password,
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
        first_name = random.choice(['Magnificent', 'Questionable', 'Bold', 'Hungry', 'Trustworthy', 'Valued', 'Free',
                                    'Obtuse', 'Frequentist', 'Long', 'Sinister', 'Happy', 'Safe', 'Open', 'Cool'])
        last_name = random.choice(['Panda', 'Birb', 'Doggo', 'Otter', 'Swearwolf', 'Kitty', 'Lion', 'Chimp', 'Cthulhu'])
        is_beneficiary = random.choice([True, False])

        phone = '+1' + ''.join([str(random.randint(0,10)) for i in range(0, 10)])

        user = create_transfer_account_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            organisation=organisation,
            is_beneficiary=is_beneficiary,
            is_vendor=not is_beneficiary
        )

        user.business_usage = business_usage

        return user


def get_or_create_transer_account(name, user):
    return _get_or_create_model_object(
        TransferAccount, {'name': name}, bind_to_entity=user, is_approved=True)


def seed_transfers(user_list, admin_user, token, number_of_transfers):
    print('Disbursing to users')
    for user in user_list:
        print(f'Disbursing to user {user.id}')
        create_transfer(
            amount=50,
            sender_user=admin_user,
            recipient_user=user,
            token=token,
            subtype=TransferSubTypeEnum.DISBURSEMENT
        )

    print('Creating %d transactions' % number_of_transfers)
    create_transfers(user_list, number_of_transfers, token)


def create_users_different_transer_usage(wanted_nr_users, org):
    i = 1
    user_list = []
    transer_usages = TransferUsage.query.all()
    while i < wanted_nr_users:

        print(f'Created user {i}')
        random_usage = random.choice(transer_usages)

        new_user = get_or_create_transfer_user(
            email=f'user_{i}@org{org.id}.com',
            business_usage=random_usage,
            organisation=org
        )

        user_list.append(new_user)
        i += 1

        db.session.commit()
    return user_list


def create_transfer(amount, sender_user, recipient_user, token, subtype=None):
    transfer = CreditTransfer(
        amount=amount,
        sender_user=sender_user,
        recipient_user=recipient_user,
        token=token,
        uuid=str(uuid4()))

    db.session.add(transfer)

    transfer.resolve_as_completed()

    transfer.transfer_type = TransferTypeEnum.PAYMENT
    transfer.transfer_subtype = subtype

    # Commit to prevent memory errors with large numbers of txns counts
    db.session.commit()

    return transfer


def create_transfers(user_list, wanted_nr_transfers, token):
    transfer_list = []
    i = 0
    while i < wanted_nr_transfers:
        print(f'Created transfer {i}')

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

            # Commit to prevent memory errors with large numbers of txns counts
            db.session.commit()
        except:
            pass
    return transfer_list


def _get_or_create_model_object(obj_class: db.Model, filter_kwargs: dict, **kwargs):

    instance = obj_class.query.filter_by(**filter_kwargs).first()

    if instance:
        return instance
    else:
        instance = obj_class(**{**filter_kwargs, **kwargs})
        db.session.add(instance)
        return instance


def create_dev_data(organisation_id, data_size):
    app = create_app()
    ctx = app.app_context()
    ctx.push()

    size_dict = data_size_options[data_size]

    # To simplify creation, we set the flask context to show all model data
    g.show_all = True

    organisation = Organisation.query.get(organisation_id)

    if organisation is None:
        raise Exception(f"Organisation not found for ID {organisation_id}")

    admin_user = User.query.filter_by(email=str('admin@acme.org').lower()).first()

    token = organisation.token

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
    user_list = create_users_different_transer_usage(size_dict['users'], organisation)

    print('Making Bulk Transfers')
    seed_transfers(user_list, admin_user, token, size_dict['transfers'])

    # TODO: Create Exchanges between different currencies

    db.session.commit()
    ctx.pop()


if __name__ == '__main__':
    # Creates dev data for the master org
    create_dev_data(1, 'small')

    if len(sys.argv) > 1:
        # Creates dev data for the secondary org
        create_dev_data(2, sys.argv[1])

