import pytest
from faker.providers import phone_number
from faker import Faker
from functools import partial

import config
from helpers.ussd_utils import create_transfer_account_for_user, make_kenyan_phone
from migrations.seed import create_ussd_menus, create_business_categories
from helpers.factories import UserFactory, TransferUsageFactory, OrganisationFactory
from server.models.credit_transfer import CreditTransfer
from server.models.token import Token
from server.models.transfer_usage import TransferUsage
from server.models.user import User
from server.models.ussd import UssdSession
from server.utils.credit_transfer import make_payment_transfer
from server.utils.user import default_transfer_account

fake = Faker()
fake.add_provider(phone_number)
phone = partial(fake.msisdn)


@pytest.fixture(scope='module')
def init_seed(test_client, init_database):
    create_ussd_menus()
    create_business_categories()


def test_golden_path_send_token(mocker, test_client,
                                init_database, initialised_blockchain_network, init_seed):
    token = Token.query.filter_by(symbol="SM1").first()
    org = OrganisationFactory()
    sender = UserFactory(preferred_language="en", phone=make_kenyan_phone(phone()), first_name="Bob", last_name="Foo",
                         pin_hash=User.salt_hash_secret('0000'), default_organisation=org)
    create_transfer_account_for_user(sender, token, 4220)

    recipient = UserFactory(preferred_language="sw", phone=make_kenyan_phone(phone()),
                            first_name="Joe", last_name="Bar", default_organisation=org)
    create_transfer_account_for_user(recipient, token, 1980)

    messages = []
    session_id = 'ATUid_05af06225e6163ec2dc9dc9cf8bc97aa'

    usage = TransferUsage.query.filter_by(name="Education").first()
    # do two of these transfers to ensure education is the first shown
    make_payment_transfer(100, token=token, send_user=sender,
                          receive_user=recipient,
                          transfer_use=str(int(usage.id)), is_ghost_transfer=False,
                          require_sender_approved=False, require_recipient_approved=False)

    make_payment_transfer(100, token=token, send_user=sender,
                          receive_user=recipient,
                          transfer_use=str(int(usage.id)), is_ghost_transfer=False,
                          require_sender_approved=False, require_recipient_approved=False)

    def mock_send_message(phone, message):
        messages.append({'phone': phone, 'message': message})
    mocker.patch('server.message_processor.send_message', mock_send_message)

    def req(text):
        response = test_client.post(
            f'/api/v1/ussd/kenya?username={config.EXTERNAL_AUTH_USERNAME}&password={config.EXTERNAL_AUTH_PASSWORD}',
            headers=dict(Accept='application/json'),
            json={'sessionId': session_id,
                  'phoneNumber': sender.phone,
                  'text': text,
                  'serviceCode': '*384*23216#'
                  }
        )
        assert response.status_code == 200
        return response.data.decode("utf-8")

    def get_session():
        return UssdSession.query.filter_by(session_id=session_id).first()

    assert get_session() is None
    resp = req("")
    assert get_session() is not None
    assert "CON Welcome" in resp

    resp = req("1")
    assert "CON Enter Phone" in resp

    resp = req(recipient.phone)
    assert "CON Enter Amount" in resp

    resp = req("12.5")
    assert "CON Select Transfer" in resp
    assert "1. Education" in resp
    assert "9." in resp

    resp = req("9")
    assert "CON Please specify" in resp
    assert "10. Show previous options" in resp
    assert "9." not in resp

    resp = req("1")
    assert "CON Please enter your PIN" in resp

    resp = req("0000")
    assert "CON Send 12.5 SM1" in resp
    # went to second page, should not be education
    assert "for Education" not in resp

    resp = req("1")
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
