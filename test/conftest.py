import pytest

from flask import current_app
from server import create_app, db
from server.utils.auth import get_complete_auth_token
# from app.manage import manager


# ---- https://www.patricksoftwareblog.com/testing-a-flask-application-using-pytest/
# ---- https://medium.com/@bfortuner/python-unit-testing-with-pytest-and-mock-197499c4623c

@pytest.fixture(scope='function')
def requires_auth(test_client):
    from server.utils.auth import requires_auth
    return requires_auth

@pytest.fixture(scope='module')
def create_blockchain_token(test_client, init_database):
    from server.models.models import Token
    token = Token(address='0xc1275b7de8af5a38a93548eb8453a498222c4ff2',
                  name='BAR Token',
                  symbol='BAR')

    db.session.add(token)
    db.session.commit()

    return token

@pytest.fixture(scope='module')
def create_organisation(test_client, init_database, create_blockchain_token):
    from server.models.models import Organisation
    organisation = Organisation(name='Sempo', token=create_blockchain_token)
    db.session.add(organisation)
    db.session.commit()
    return organisation

@pytest.fixture(scope='module')
def new_sempo_admin_user():
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
    from server.models.transfer import TransferAccount
    return TransferAccount()

@pytest.fixture(scope='module')
def create_transfer_account(new_transfer_account):
    db.session.add(new_transfer_account)
    db.session.commit()
    return new_transfer_account

@pytest.fixture(scope='module')
def new_disbursement(create_transfer_account_user):
    from server.utils.credit_transfers import make_disbursement_transfer
    disbursement = make_disbursement_transfer(100,create_transfer_account_user)
    return disbursement

@pytest.fixture(scope='function')
def new_credit_transfer(create_transfer_account_user, create_blockchain_token):
    from server.models.transfer import CreditTransfer
    credit_transfer = CreditTransfer(
        amount=100,
        token=create_blockchain_token,
        sender=create_transfer_account_user,
        recipient=create_transfer_account_user
    )
    return credit_transfer

@pytest.fixture(scope='function')
def create_credit_transfer(new_credit_transfer):
    db.session.add(new_credit_transfer)
    db.session.commit()
    return new_credit_transfer


@pytest.fixture(scope='function')
def proccess_phone_number(test_client):
    from server.utils.phone import proccess_phone_number
    return proccess_phone_number


@pytest.fixture(scope='function')
def save_device_info(test_client, init_database, create_transfer_account_user):
    from server.utils.user import save_device_info
    return save_device_info


@pytest.fixture(scope='function')
def create_blacklisted_token(authed_sempo_admin_user):
    from server.models.models import BlacklistToken
    auth_token = authed_sempo_admin_user.encode_auth_token().decode()
    blacklist_token = BlacklistToken(token=auth_token)
    db.session.add(blacklist_token)
    db.session.commit()
    return blacklist_token


@pytest.fixture(scope='function')
def create_transfer_usage(test_client, init_database):
    from server.models.models import TransferUsage
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
        db.session.close_all()  # DO NOT DELETE THIS LINE. We need to close sessions before dropping tables.
        db.drop_all()
