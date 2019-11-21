import pytest
from flask import current_app
from faker.providers import phone_number
from faker import Faker

from sqlalchemy.exc import ProgrammingError
import os
import sys
app_dir = os.path.abspath(os.path.join(os.getcwd(), "app"))
sys.path.append(app_dir)
sys.path.append(os.getcwd())

from server import create_app, db
from server.utils.auth import get_complete_auth_token
import config
# from app.manage import manager

fake = Faker()
fake.add_provider(phone_number)

# ---- https://www.patricksoftwareblog.com/testing-a-flask-application-using-pytest/
# ---- https://medium.com/@bfortuner/python-unit-testing-with-pytest-and-mock-197499c4623c

@pytest.fixture(scope='function')
def requires_auth(test_client):
    from server.utils.auth import requires_auth
    return requires_auth

@pytest.fixture(scope='module')
def create_master_organisation(test_client, init_database):
    from server.models.organisation import Organisation
    master_organisation = Organisation.query.filter_by(is_master=True).first()
    if master_organisation is None:
        print('Creating master organisation')
        master_organisation = Organisation(is_master=True)
        db.session.add(master_organisation)

        db.session.commit()

    return master_organisation

@pytest.fixture(scope='module')
def create_organisation(test_client, init_database, external_reserve_token):
    from server.models.organisation import Organisation
    from server.models.transfer_account import TransferAccount
    organisation = Organisation(name='Sempo', token=external_reserve_token)

    db.session.add(organisation)
    db.session.commit()

    return organisation

@pytest.fixture(scope='module')
def new_sempo_admin_user(test_client, init_database, create_organisation):
    from server.models.user import User
    user = User()
    user.create_admin_auth(email='tristan@sempo.ai', password='TestPassword', tier='sempoadmin')
    user.organisations.append(create_organisation)
    user.default_organisation = create_organisation

    db.session.add(user)

    # Commit so it gets an ID
    db.session.commit()

    return user


@pytest.fixture(scope='module')
def authed_sempo_admin_user(new_sempo_admin_user):
    """
    Returns a sempo admin user that is activated and has TFA set up
    """

    new_sempo_admin_user.is_activated = True
    new_sempo_admin_user.set_TFA_secret()
    new_sempo_admin_user.TFA_enabled = True


    return new_sempo_admin_user

@pytest.fixture(scope='module')
def activated_sempo_admin_user(new_sempo_admin_user):
    """
    Returns a sempo admin user that is activated but does NOT have TFA set up
    """

    new_sempo_admin_user.is_activated = True
    # Commit the changes for the users
    db.session.commit()

    return new_sempo_admin_user


@pytest.fixture(scope='function')
def complete_admin_auth_token(authed_sempo_admin_user):
    return get_complete_auth_token(authed_sempo_admin_user)


@pytest.fixture(scope='module')
def create_transfer_account_user(test_client, init_database, create_organisation):
    from server.utils.user import create_transfer_account_user
    user = create_transfer_account_user(first_name='Transfer',
                                        last_name='User',
                                        phone=fake.msisdn(),
                                        organisation=create_organisation)
    db.session.commit()
    return user


@pytest.fixture(scope='module')
def create_user_with_existing_transfer_account(test_client, init_database, create_transfer_account):
    from server.utils.user import create_transfer_account_user
    user = create_transfer_account_user(first_name='Existing Transfer', last_name='User',
                                        phone=fake.msisdn(),
                                        existing_transfer_account=create_transfer_account)
    db.session.commit()
    return user


@pytest.fixture(scope='module')
def new_transfer_account(create_master_organisation):
    from server.models.transfer_account import TransferAccount
    return TransferAccount()


@pytest.fixture(scope='module')
def create_transfer_account(new_transfer_account):
    db.session.add(new_transfer_account)
    db.session.commit()
    return new_transfer_account


@pytest.fixture(scope='module')
def new_disbursement(create_transfer_account_user):
    from server.utils.credit_transfer import make_payment_transfer
    disbursement = make_payment_transfer(100, receive_transfer_account=create_transfer_account_user, transfer_subtype='DISBURSEMENT')
    return disbursement


@pytest.fixture(scope='function')
def new_credit_transfer(create_transfer_account_user, external_reserve_token):
    from server.models.credit_transfer import CreditTransfer
    credit_transfer = CreditTransfer(
        amount=1000,
        token=external_reserve_token,
        sender_user=create_transfer_account_user,
        recipient_user=create_transfer_account_user,
        transfer_type='PAYMENT'
    )
    return credit_transfer


@pytest.fixture(scope='function')
def create_credit_transfer(new_credit_transfer):
    db.session.add(new_credit_transfer)
    db.session.commit()
    return new_credit_transfer


@pytest.fixture(scope='function')
def proccess_phone_number_with_ctx(test_client):
    from server.utils.phone import proccess_phone_number
    return proccess_phone_number


@pytest.fixture(scope='function')
def save_device_info(test_client, init_database, create_transfer_account_user):
    from server.utils.user import save_device_info
    return save_device_info


@pytest.fixture(scope='function')
def create_blacklisted_token(authed_sempo_admin_user):
    from server.models.blacklist_token import BlacklistToken
    auth_token = authed_sempo_admin_user.encode_auth_token().decode()
    blacklist_token = BlacklistToken(token=auth_token)
    db.session.add(blacklist_token)
    db.session.commit()
    return blacklist_token


@pytest.fixture(scope='function')
def create_transfer_usage(test_client, init_database):
    from server.models.transfer_usage import TransferUsage
    instance = TransferUsage.query.filter_by(name='Food').first()
    if instance:
        return instance
    transfer_usage = TransferUsage(name='Food', icon='food-apple', translations=dict(en='Food', fr='aliments'))
    db.session.add(transfer_usage)
    db.session.commit()
    return transfer_usage


@pytest.fixture(scope='function')
def create_ip_address(authed_sempo_admin_user):
    from server.models.ip_address import IpAddress
    ip_address = IpAddress(ip="210.18.192.196")
    ip_address.user = authed_sempo_admin_user
    db.session.add(ip_address)
    db.session.commit()
    return ip_address


@pytest.fixture(scope='function')
def create_fiat_ramp():
    from server.models.fiat_ramp import FiatRamp
    fiat_ramp = FiatRamp(
            payment_method='POLI',
            payment_amount=int(100),
        )
    db.session.add(fiat_ramp)
    db.session.commit()
    return fiat_ramp


@pytest.fixture(scope='module')
def admin_with_org_reserve_balance(authed_sempo_admin_user, external_reserve_token, loaded_master_wallet_address):
    from server import bt

    amount = 100

    org_transfer_account = authed_sempo_admin_user.default_organisation.org_level_transfer_account

    org_transfer_account.balance = amount

    bt.make_token_transfer(
        loaded_master_wallet_address,
        org_transfer_account.token,
        loaded_master_wallet_address, org_transfer_account.blockchain_address,
        amount)

    return authed_sempo_admin_user


@pytest.fixture(scope='module')
def user_with_reserve_balance(create_transfer_account_user, external_reserve_token, loaded_master_wallet_address):
    from server import bt

    amount = 100

    transfer_account = create_transfer_account_user.get_transfer_account_for_token(external_reserve_token)

    bt.make_token_transfer(loaded_master_wallet_address,
                        transfer_account.token,
                        loaded_master_wallet_address, transfer_account.blockchain_address,
                        amount)

    transfer_account.balance = amount
    create_transfer_account_user.is_activated = True

    return create_transfer_account_user

@pytest.fixture(scope='module')
def initialised_blockchain_network(
        create_master_organisation, admin_with_org_reserve_balance, external_reserve_token, load_account):

    from server import bt

    from server.models.token import Token
    from server.models.exchange import ExchangeContract

    reserve_token = external_reserve_token

    def deploy_and_add_smart_token(name, symbol, reserve_ratio_ppm, exchange_contract=None):
        smart_token_result = bt.deploy_smart_token(
            deploying_address=deploying_address,
            name=name, symbol=symbol, decimals=18,
            reserve_deposit_wei=10,
            issue_amount_wei=1000,
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

        return smart_token, exchange_contract

    organisation = admin_with_org_reserve_balance.organisations[0]
    deploying_address = organisation.org_level_transfer_account.blockchain_address
    # Load admin's *system* blockchain account with Eth
    load_account(organisation.system_blockchain_address)

    # Load admin org blockchain account with with Eth
    load_account(deploying_address)

    # Create reserve token


    # Initialise an exchange network
    registry_address = bt.deploy_exchange_network(deploying_address)

    # Create first smart token and add to exchange network
    (smart_token_1,
     exchange_contract) = deploy_and_add_smart_token('Smart Token 1', 'SM1', 250000)

    # Create second smart token and add to exchange network
    (smart_token_2,
     exchange_contract) = deploy_and_add_smart_token('Smart Token 2', 'SM1', 250000, exchange_contract)

    db.session.commit()

    return {
        'exchange_contract': exchange_contract,
        'reserve_token': reserve_token,
        'smart_token_1': smart_token_1,
        'smart_token_2': smart_token_2
    }


@pytest.fixture(scope='module')
def loaded_master_wallet_address(load_account):
    """
    A blockchain address that isn't tracked in the Sempo system like a regular one. Used during testing
    for deploying blockchain components that are normally controlled by an external entity, eg reserve tokens
    """
    from server import bt

    deploying_address = bt.create_blockchain_wallet(private_key=config.MASTER_WALLET_PRIVATE_KEY)

    load_account(deploying_address)

    return deploying_address


@pytest.fixture(scope='module')
def external_reserve_token(test_client, init_database, loaded_master_wallet_address):
    from server.models.token import Token
    from server import bt

    name = "AUD Reserve Token"
    symbol = "AUD"

    reserve_token_address = bt.deploy_and_fund_reserve_token(
        deploying_address=loaded_master_wallet_address,
        name=name,
        symbol=symbol,
        fund_amount_wei=4 * 10 ** 18
    )

    reserve_token = Token(address=reserve_token_address, name=name, symbol=symbol, token_type='RESERVE')
    reserve_token.decimals = 18

    db.session.add(reserve_token)
    db.session.commit()

    return reserve_token


@pytest.fixture(scope='module')
def test_request_context():
    flask_app = create_app()

    # can be used in combination with the WITH statement to activate a request context temporarily.
    # with this you can access the request, g and session objects in view functions
    yield flask_app.test_request_context


@pytest.fixture(scope='module')
def test_client():
    flask_app = create_app()

    # Flask provides a way to test your application by exposing the Werkzeug test Client
    # and handling the context locals for you.
    testing_client = flask_app.test_client()

    # Establish an application context before running the tests.
    ctx = flask_app.app_context()
    ctx.push()

    yield testing_client  # this is where the testing happens!

    ctx.pop()


@pytest.fixture(scope='module')
def init_database():
    # Create the database and the database table

    with current_app.app_context():
        db.create_all()  # todo- use manage.py

    yield db  # this is where the testing happens!

    with current_app.app_context():
        db.session.remove()  # DO NOT DELETE THIS LINE. We need to close sessions before dropping tables.
        db.drop_all()

@pytest.fixture(scope="module")
def monkeymodule(request):
    from _pytest.monkeypatch import MonkeyPatch
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()