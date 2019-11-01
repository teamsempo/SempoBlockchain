import pytest
from flask import current_app
from sqlalchemy.exc import ProgrammingError
import os
import sys
app_dir = os.path.abspath(os.path.join(os.getcwd(), "app"))
sys.path.append(app_dir)
sys.path.append(os.getcwd())

from web3 import (
    Web3,
    WebsocketProvider,
    HTTPProvider
)

from server import create_app, db
from server.utils.auth import get_complete_auth_token
import config
# from app.manage import manager


# ---- https://www.patricksoftwareblog.com/testing-a-flask-application-using-pytest/
# ---- https://medium.com/@bfortuner/python-unit-testing-with-pytest-and-mock-197499c4623c

@pytest.fixture(scope='function')
def requires_auth(test_client):
    from server.utils.auth import requires_auth
    return requires_auth


@pytest.fixture(scope='module')
def create_blockchain_token(test_client, init_database):
    from server.models.token import Token
    token = Token(address='0xc1275b7de8af5a38a93548eb8453a498222c4ff2',
                  name='AUD Token',
                  symbol='AUD')

    db.session.add(token)
    db.session.commit()

    return token


@pytest.fixture(scope='module')
def create_organisation(test_client, init_database, create_blockchain_token):
    from server.models.organisation import Organisation
    organisation = Organisation(name='Sempo', token=create_blockchain_token)
    db.session.add(organisation)
    db.session.commit()
    return organisation


@pytest.fixture(scope='module')
def new_sempo_admin_user(test_client):
    from server.models.user import User
    user = User()
    user.create_admin_auth(email='tristan@sempo.ai', password='TestPassword', tier='sempoadmin')
    return user


@pytest.fixture(scope='module')
def create_unactivated_sempo_admin_user(test_client, init_database, new_sempo_admin_user, create_organisation):
    db.session.add(new_sempo_admin_user)
    new_sempo_admin_user.organisations.append(create_organisation)

    # Commit the changes for the users
    db.session.commit()

    return new_sempo_admin_user


@pytest.fixture(scope='module')
def activated_sempo_admin_user(create_unactivated_sempo_admin_user):
    """
    Returns a sempo admin user that is activated but does NOT have TFA set up
    """

    create_unactivated_sempo_admin_user.is_activated = True
    # Commit the changes for the users
    db.session.commit()

    return create_unactivated_sempo_admin_user


@pytest.fixture(scope='module')
def authed_sempo_admin_user(create_unactivated_sempo_admin_user):
    """
    Returns a sempo admin user that is activated and has TFA set up
    """

    create_unactivated_sempo_admin_user.is_activated = True
    create_unactivated_sempo_admin_user.set_TFA_secret()
    create_unactivated_sempo_admin_user.TFA_enabled = True

    # Commit the changes for the users
    db.session.commit()

    return create_unactivated_sempo_admin_user


@pytest.fixture(scope='function')
def complete_auth_token(authed_sempo_admin_user):
    return get_complete_auth_token(authed_sempo_admin_user)


@pytest.fixture(scope='module')
def create_transfer_account_user(test_client, init_database, create_organisation):
    from server.utils.user import create_transfer_account_user
    user = create_transfer_account_user(first_name='Transfer',
                                        last_name='User',
                                        phone='0400000000',
                                        organisation=create_organisation)
    db.session.commit()
    return user


@pytest.fixture(scope='module')
def create_user_with_existing_transfer_account(test_client, init_database, create_transfer_account):
    from server.utils.user import create_transfer_account_user
    user = create_transfer_account_user(first_name='Existing Transfer', last_name='User',
                                        phone='0400000000', existing_transfer_account=create_transfer_account)
    db.session.commit()
    return user


@pytest.fixture(scope='module')
def new_transfer_account():
    from server.models.transfer_account import TransferAccount
    return TransferAccount()


@pytest.fixture(scope='module')
def create_transfer_account(new_transfer_account):
    db.session.add(new_transfer_account)
    db.session.commit()
    return new_transfer_account


@pytest.fixture(scope='module')
def new_disbursement(create_transfer_account_user):
    from server.utils.credit_transfers import make_payment_transfer
    disbursement = make_payment_transfer(100, receive_transfer_account=create_transfer_account_user, transfer_subtype='DISBURSEMENT')
    return disbursement


@pytest.fixture(scope='function')
def new_credit_transfer(create_transfer_account_user, create_blockchain_token):
    from server.models.credit_transfer import CreditTransfer
    credit_transfer = CreditTransfer(
        amount=100,
        token=create_blockchain_token,
        sender_user=create_transfer_account_user,
        recipient_user=create_transfer_account_user
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
def initialise_blockchain_network(authed_sempo_admin_user):

    w3 = Web3(HTTPProvider(config.ETH_HTTP_PROVIDER))

    def load_account(address):

        tx_hash = w3.eth.sendTransaction(
            {'to': address, 'from': w3.eth.accounts[0], 'value': 12345})

        return w3.eth.waitForTransactionReceipt(tx_hash)

    # Load admin's *system* blockchain account with Eth
    load_account(111)

    # Load admin blockchain account with with Eth

    # Create reserve token

    # Initialise an exchange network

    # Create first smart token and add to exchange network

    # Create second smart token and add to exchange network



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
