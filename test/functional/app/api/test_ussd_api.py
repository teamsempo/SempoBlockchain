import json
from faker.providers import phone_number
from faker import Faker
from functools import partial
from flask import g

import config
from helpers.ussd_utils import create_transfer_account_for_user, make_kenyan_phone
from helpers.factories import UserFactory, TransferUsageFactory, OrganisationFactory
from server.models.token import Token
from server.models.transfer_usage import TransferUsage
from server.models.user import User, RegistrationMethodEnum
from server.models.ussd import UssdSession
from server.utils.credit_transfer import make_payment_transfer
from server.utils.user import default_transfer_account, create_user_without_transfer_account
from server.utils.auth import get_complete_auth_token

fake = Faker()
fake.add_provider(phone_number)
phone = partial(fake.msisdn)
unregistered_user_phone = make_kenyan_phone(phone())

# TODO make helper functions and messages array fixture object
messages = []
session_id = 'ATUid_05af06225e6163ec2dc9dc9cf8bc97aa'
valid_service_code = config.USSD_VALID_SERVICE_CODE


def mock_send_message(phone, message):
    messages.append({'phone': phone, 'message': message})


def req(text,
        client,
        sender_phone,
        service_code=None,
        session_id=session_id,
        auth_username=config.EXTERNAL_AUTH_USERNAME,
        auth_password=config.EXTERNAL_AUTH_PASSWORD):
    if service_code is None:
        service_code = valid_service_code
    response = client.post(
        f'/api/v1/ussd/kenya?username={auth_username}&password={auth_password}',
        headers=dict(Accept='application/json'),
        json={'sessionId': session_id,
              'phoneNumber': sender_phone,
              'text': text,
              'serviceCode': service_code,
              }
    )
    assert response.status_code == 200
    return response.data.decode("utf-8")


def get_session():
    return UssdSession.query.filter_by(session_id=session_id).first()


def test_golden_path_send_token(mocker, test_client, init_database, initialised_blockchain_network, init_seed):
    token = Token.query.filter_by(symbol="SM1").first()
    org = OrganisationFactory(country_code=config.DEFAULT_COUNTRY)
    sender = UserFactory(preferred_language="en",
                         phone=make_kenyan_phone(phone()),
                         first_name="Bob",
                         last_name="Foo",
                         pin_hash=User.salt_hash_secret('0000'),
                         default_organisation=org)
    create_transfer_account_for_user(sender, token, 4220)

    recipient = UserFactory(preferred_language="sw",
                            phone=make_kenyan_phone(phone()),
                            first_name="Joe",
                            last_name="Bar",
                            default_organisation=org)
    create_transfer_account_for_user(recipient, token, 1980)

    usages = TransferUsage.query.filter_by(default=True).order_by(TransferUsage.priority).all()
    top_priority = usages[0]
    # Take the last to ensure that we're not going to simply reinforce the existing order
    usage = usages[-1]
    # do two of these transfers to ensure last is is the first shown
    make_payment_transfer(100,
                          token=token,
                          send_user=sender,
                          receive_user=recipient,
                          transfer_use=str(int(usage.id)),
                          is_ghost_transfer=False,
                          require_sender_approved=False,
                          require_recipient_approved=False)

    make_payment_transfer(100,
                          token=token,
                          send_user=sender,
                          receive_user=recipient,
                          transfer_use=str(int(usage.id)),
                          is_ghost_transfer=False,
                          require_sender_approved=False,
                          require_recipient_approved=False)

    def mock_send_message(phone, message):
        messages.append({'phone': phone, 'message': message})

    mocker.patch(f'server.utils.phone._send_twilio_message.submit', mock_send_message)
    mocker.patch(f'server.utils.phone._send_messagebird_message.submit', mock_send_message)
    mocker.patch(f'server.utils.phone._send_at_message.submit', mock_send_message)

    assert get_session() is None
    resp = req("", test_client, sender.phone)
    assert get_session() is not None
    assert "CON Welcome" in resp

    resp = req("1", test_client, sender.phone)
    assert "CON Enter Phone" in resp

    resp = req(recipient.phone, test_client, sender.phone)
    assert "CON Enter Amount" in resp

    resp = req("12.5", test_client, sender.phone)
    assert "CON Send 12.5 SM1" in resp

    resp = req("0000", test_client, sender.phone)
    assert "END Your request has been sent." in resp

    assert default_transfer_account(sender).balance == (4220 - 100 - 100 - 1250)
    assert default_transfer_account(recipient).balance == (1980 + 100 + 100 + 1250)

    assert len(messages) == 3
    sent_message = messages[1]
    assert sent_message['phone'] == sender.phone
    assert f"sent a payment of 12.50 SM1 to {recipient.first_name}" in sent_message['message']
    received_message = messages[2]
    assert received_message['phone'] == recipient.phone
    assert f"Umepokea 12.50 SM1 kutoka kwa {sender.first_name}" in received_message['message']


def test_invalid_service_code(mocker, test_client, init_database, initialised_blockchain_network, init_seed):
    org = OrganisationFactory()
    sender = UserFactory(preferred_language="en",
                         phone=make_kenyan_phone(phone()),
                         first_name="Bob",
                         last_name="Foo",
                         pin_hash=User.salt_hash_secret('0000'), default_organisation=org)

    resp = req("", test_client, sender.phone, '*42*666#')
    assert 'END Bonyeza {} kutumia mtandao'.format(valid_service_code) in resp


def test_ussd_self_signup_flow(test_client,
                               init_database,
                               init_seed,
                               create_temporary_user,
                               create_organisation):
    # create organisation
    organisation = create_organisation
    organisation.external_auth_password = config.EXTERNAL_AUTH_PASSWORD

    # define username to match the external_auth_username as defined in : /app/migrations/versions/961ab9adc300_.py
    external_auth_username = 'admin_' + (organisation.name or '').lower().replace(' ', '_')

    # set active organisation
    g.active_organisation = organisation

    resp = req("", test_client, unregistered_user_phone)
    assert "CON Welcome to Sarafu" in resp

    user = create_temporary_user

    resp = req("1", test_client, user.phone, auth_username=external_auth_username)
    assert "CON Please enter a PIN" in resp

    resp = req("0000", test_client, user.phone, auth_username=external_auth_username)
    assert "CON Enter your PIN again" in resp

    resp = req("0000", test_client, user.phone, auth_username=external_auth_username)
    assert "END Your account is being created." in resp
    assert user.first_name == 'Unknown first name'
    assert user.last_name == 'Unknown last name'
    bio = next(filter(lambda x: x.name == 'bio', user.custom_attributes), None)
    assert bio.value == 'Unknown business'
    gender = next(filter(lambda x: x.name == 'gender', user.custom_attributes), None)
    assert gender.value == 'Unknown gender'
    assert user.location == 'Unknown location'


def test_ussd_self_signup_wrong_pin_entry(test_client,
                                          init_database,
                                          create_temporary_user,
                                          create_organisation):
    # create organisation
    organisation = create_organisation
    organisation.external_auth_password = config.EXTERNAL_AUTH_PASSWORD

    # define username to match the external_auth_username as defined in : /app/migrations/versions/961ab9adc300_.py
    external_auth_username = 'admin_' + (organisation.name or '').lower().replace(' ', '_')

    # set active organisation
    g.active_organisation = organisation
    other_unregistered_user_phone = '+611256465214'

    resp = req("", test_client, other_unregistered_user_phone)
    assert "CON Welcome to Sarafu" in resp

    # create self signup user
    user = UserFactory(id=22,
                       phone=other_unregistered_user_phone,
                       first_name='Unknown first name',
                       last_name='Unknown last name',
                       registration_method=RegistrationMethodEnum.USSD_SIGNUP)

    resp = req("1", test_client, user.phone, auth_username=external_auth_username)
    assert "CON Please enter a PIN" in resp

    resp = req("0000", test_client, user.phone, auth_username=external_auth_username)
    assert "CON Enter your PIN again" in resp

    resp = req("1212", test_client, user.phone, auth_username=external_auth_username)
    assert "END The new PIN does not match the one you entered." in resp


def test_reset_pin_flow(test_client,
                        init_database,
                        create_organisation,
                        authed_sempo_admin_user):

    # define different session id
    other_session_id = 'ATUid_05af06225e6163ec2dc9dc9cf8bc97aa000'

    # create organisation
    organisation = create_organisation
    organisation.external_auth_password = config.EXTERNAL_AUTH_PASSWORD

    # create highest tier admin
    admin = authed_sempo_admin_user
    admin.set_held_role('ADMIN', 'sempoadmin')

    # get admin's auth token
    auth = get_complete_auth_token(authed_sempo_admin_user)

    # create self signup user
    user = UserFactory(id=21,
                       phone='+6185274136',
                       first_name='Unknown first name',
                       last_name='Unknown last name',
                       pin_hash=User.salt_hash_secret('0000'),
                       failed_pin_attempts=0,
                       preferred_language="en",
                       registration_method=RegistrationMethodEnum.USSD_SIGNUP)

    # bind user to organisation
    user.add_user_to_organisation(organisation, False)

    # reset pin as admin
    response = test_client.post(
        '/api/v1/user/reset_pin/',
        headers=dict(
            Authorization=auth,
            Accept='application/json'
        ),
        content_type='application/json',
        json={
            'user_id': user.id
        }
    )
    assert response.status_code == 200
    assert len(user.pin_reset_tokens) > 0

    # test user's reset process
    ussd_resp = req("", test_client, user.phone, session_id=other_session_id)
    assert "CON Please enter a PIN to manage your account." in ussd_resp

    ussd_resp = req("1212", test_client, user.phone, session_id=other_session_id)
    assert "CON Enter your PIN again" in ussd_resp

    ussd_resp = req("1212", test_client, user.phone, session_id=other_session_id)
    assert "CON Welcome to Sarafu" in ussd_resp
