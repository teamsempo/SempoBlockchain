import pytest
from time import sleep

from flask import current_app
from faker.providers import phone_number
from faker import Faker

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from server import create_app, db
from server.utils.auth import get_complete_auth_token
from server.models.token import TokenType
from server.utils.transfer_enums import TransferTypeEnum, TransferSubTypeEnum
import config
# from app.manage import manager

fake = Faker()
fake.add_provider(phone_number)

# ---- https://www.patricksoftwareblog.com/testing-a-flask-application-using-pytest/
# ---- https://medium.com/@bfortuner/python-unit-testing-with-pytest-and-mock-197499c4623c

@pytest.fixture(scope='session', autouse=True)
def wait_for_worker_boot_if_needed():
    TIMEOUT = 60

    from server.utils.celery_utils import get_celery_worker_status
    from helpers.utils import will_func_test_blockchain

    if will_func_test_blockchain():

        elapsed = 0
        while elapsed < TIMEOUT:
            worker_status = get_celery_worker_status()
            if 'ERROR' not in worker_status:
                print("Celery Workers Found")
                return
            sleep(1)
            elapsed += 1

        raise Exception("Timeout while waiting for celery workers")
    else:
        print("Not testing blockchain; not waiting for celery workers")
        return

@pytest.fixture(scope='function')
def requires_auth(test_client):
    from server.utils.auth import requires_auth
    return requires_auth

@pytest.fixture(scope='module')
def create_master_organisation(test_client, init_database, external_reserve_token):
    from server.models.organisation import Organisation
    master_organisation = Organisation.master_organisation()
    if master_organisation is None:
        print('Creating master organisation')
        master_organisation = Organisation(name='FrancineCorp', is_master=True, token=external_reserve_token,
                                           country_code='AU')
        db.session.add(master_organisation)
        db.session.commit()

    return master_organisation

@pytest.fixture(scope='module')
def create_organisation(test_client, init_database, external_reserve_token, create_master_organisation):
    from server.models.organisation import Organisation
    organisation = Organisation(name='Sempo', token=external_reserve_token, default_disbursement=400, country_code='US')
    db.session.add(organisation)
    db.session.commit()

    return organisation

@pytest.fixture(scope='module')
def new_sempo_admin_user(test_client, init_database, create_organisation):
    from server.models.user import User
    user = User()
    user.create_admin_auth(email='tristan@withsempo.com', password='TestPassword', tier='sempoadmin')
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

create_transfer_account_user_2 = create_transfer_account_user

@pytest.fixture(scope='function')
def create_transfer_account_user_function(test_client, init_database, create_organisation):
    from server.utils.user import create_transfer_account_user
    user = create_transfer_account_user(first_name='Transfer',
                                        last_name='User 2',
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
    disbursement = make_payment_transfer(
        100,
        receive_transfer_account=create_transfer_account_user,
        transfer_subtype=TransferSubTypeEnum.DISBURSEMENT
    )
    return disbursement


@pytest.fixture(scope='function')
def new_credit_transfer(create_transfer_account_user, create_transfer_account_user_2, external_reserve_token):
    from server.models.credit_transfer import CreditTransfer
    from uuid import uuid4

    credit_transfer = CreditTransfer(
        amount=1000,
        token=external_reserve_token,
        sender_user=create_transfer_account_user,
        recipient_user=create_transfer_account_user_2,
        transfer_type=TransferTypeEnum.PAYMENT,
        transfer_subtype=TransferSubTypeEnum.STANDARD,
        uuid=str(uuid4()),
        require_sufficient_balance=False
    )
    return credit_transfer

@pytest.fixture(scope='function')
def other_new_credit_transfer(create_transfer_account_user, external_reserve_token):
    # Janky copy paste job because of how pytest works
    from server.models.credit_transfer import CreditTransfer
    from uuid import uuid4

    credit_transfer = CreditTransfer(
        amount=1000,
        token=external_reserve_token,
        sender_user=create_transfer_account_user,
        recipient_user=create_transfer_account_user,
        transfer_type=TransferTypeEnum.PAYMENT,
        transfer_subtype=TransferSubTypeEnum.STANDARD,
        uuid=str(uuid4()),
        require_sufficient_balance=False
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


@pytest.fixture(scope='module')
def create_filter(test_client, init_database, create_organisation):
    from server.models.saved_filter import SavedFilter
    saved_filter = SavedFilter(
        name='TestFilter',
        filter=dict(allowedValues=[1,2], id=1, keyName='balance', type='of'),
        organisation_id=create_organisation.id
    )
    db.session.add(saved_filter)
    db.session.commit()
    return saved_filter


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


@pytest.fixture(scope='module')
def create_fiat_ramp(test_client, init_database):
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
    org_transfer_account.set_balance_offset(amount)

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
    transfer_account.set_balance_offset(amount)
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
     exchange_contract) = deploy_and_add_smart_token('Smart Token 2', 'SM2', 250000, exchange_contract)

    (smart_token_3,
     exchange_contract) = deploy_and_add_smart_token('Smart Token 3', 'SM3', 250000, exchange_contract)

    db.session.commit()

    return {
        'exchange_contract': exchange_contract,
        'reserve_token': reserve_token,
        'smart_token_1': smart_token_1,
        'smart_token_2': smart_token_2,
        'smart_token_3': smart_token_3
    }


@pytest.fixture(scope='module')
def loaded_master_wallet_address(load_account):
    """
    A blockchain address that isn't tracked in the Sempo system like a regular one. Used during testing
    for deploying blockchain components that are normally controlled by an external entity, eg reserve tokens
    """
    from server import bt

    deploying_address = bt.create_blockchain_wallet(private_key=current_app.config['CHAINS']['ETHEREUM']['MASTER_WALLET_PRIVATE_KEY'])

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

    reserve_token = Token(address=reserve_token_address, name=name, symbol=symbol, token_type=TokenType.RESERVE)
    reserve_token.decimals = 18

    db.session.add(reserve_token)
    db.session.commit()

    return reserve_token


@pytest.fixture(scope='module')
def test_request_context():
    flask_app = create_app(skip_create_filters=True)

    # can be used in combination with the WITH statement to activate a request context temporarily.
    # with this you can access the request, g and session objects in view functions
    yield flask_app.test_request_context


@pytest.fixture(scope='module')
def test_client():
    flask_app = create_app(skip_create_filters=True)

    # Flask provides a way to test your application by exposing the Werkzeug test Client
    # and handling the context locals for you.
    testing_client = flask_app.test_client()

    # Establish an application context before running the tests.
    ctx = flask_app.app_context()
    ctx.push()

    from flask import g
    g.pending_transactions = []
    g.executor_jobs = []
    g.is_after_request = False
    yield testing_client  # this is where the testing happens!

    ctx.pop()


@pytest.fixture(scope='module')
def init_database(test_client):
    # Create the database and the database table

    with current_app.app_context():
        db.create_all()

    yield db  # this is where the testing happens!

    with current_app.app_context():
        try:
            db.session.execute('DROP MATERIALIZED VIEW IF EXISTS search_view;')
            db.session.commit()
        except:
            pass
        db.session.remove()  # DO NOT DELETE THIS LINE. We need to close sessions before dropping tables.
        db.drop_all()


@pytest.fixture(autouse=True)
def mock_sms_apis(mocker):
    # Always patch out all sms sending apis because we don't want to spam messages with our tests!!
    messages = []
    def mock_sms_api(phone, message):
        messages.append({'phone': phone, 'message': message})

    mocker.patch('server.utils.phone._send_twilio_message.submit', mock_sms_api)
    mocker.patch('server.utils.phone._send_messagebird_message.submit', mock_sms_api)
    mocker.patch('server.utils.phone._send_at_message.submit', mock_sms_api)

    return messages

@pytest.fixture(autouse=True)
def mock_pusher(mocker):
    mocker.patch('server.pusher_client.trigger')
    mocker.patch('server.pusher_client.authenticate')
    mocker.patch('server.pusher_client.trigger_batch')

@pytest.fixture(autouse=True)
def mock_osm_search(mocker):
    def mock_osm_api(query_string):
        class Response:
            def json(self):
                return self.json_response

            def __init__(self, query_string):
                if query_string == 'not a real place' or query_string == 'not a real place, Canada':
                    self.json_response = []
                elif query_string == 'multiple matched place' or query_string == 'multiple matched place, Canada':
                    self.json_response = [
                        {'lat': '12.0', 'lon': '14.4'},
                        {'lat': '-37.81', 'lon': '144.97'},
                    ]
                else:
                    self.json_response = [
                        {'lat': '-37.81', 'lon': '144.97'},
                    ]

                self.status_code = 200
                self.text = 'Yeehaaaa'

        return Response(query_string)

    mocker.patch('server.utils.location._query_osm', mock_osm_api)


@pytest.fixture(autouse=True)
def mock_amazon_ses(mocker):
    mocker.patch('server.utils.amazon_ses.ses_email_handler')

@pytest.fixture(scope="module")
def monkeymodule():
    from _pytest.monkeypatch import MonkeyPatch
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()
