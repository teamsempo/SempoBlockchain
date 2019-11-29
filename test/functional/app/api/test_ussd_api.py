import pytest
from faker.providers import phone_number
from faker import Faker
from functools import partial

from helpers.ussd_utils import create_transfer_account_for_user, make_kenyan_phone
from server import db
from helpers.user import UserFactory
from server.models.token import Token
from server.models.user import User
from server.models.ussd import UssdSession, UssdMenu
from server.utils.user import default_transfer_account

fake = Faker()
fake.add_provider(phone_number)
phone = partial(fake.msisdn)


@pytest.fixture(scope='module')
def init_menus(test_client, init_database):
    def create_menu(name, description, parent_id=None):
        instance = UssdMenu(
            name=name,
            description=description,
            display_key="ussd.kenya.{}".format(name),
            parent_id=parent_id
        )
        db.session.add(instance)
        db.session.commit()
        return instance

    start_menu = create_menu(
        name='start',
        description='Start menu. This is the entry point for activated users',
    )
    create_menu(
        name='send_enter_recipient',
        description='Send Token recipient entry',
        parent_id=start_menu.id
    )
    create_menu(
        name='send_token_amount',
        description='Send Token amount prompt menu',
        parent_id=start_menu.id
    )
    create_menu(
        name='send_token_reason',
        description='Send Token reason prompt menu',
        parent_id=start_menu.id
    )
    create_menu(
        name='send_token_reason_other',
        description='Send Token other reason prompt menu',
        parent_id=start_menu.id
    )
    create_menu(
        name='send_token_pin_authorization',
        description='PIN entry for authorization to send token',
        parent_id=start_menu.id
    )
    create_menu(
        name='send_token_confirmation',
        description='Send Token confirmation menu',
        parent_id=start_menu.id
    )
    create_menu(
        name='complete',
        description='Complete menu. Last step of any menu',
    )


def test_golden_path_send_token(mocker, test_client, init_database, initialised_blockchain_network, init_menus):
    token = Token.query.filter_by(symbol="SM1").first()
    sender = UserFactory(preferred_language="en", phone=make_kenyan_phone(phone()), first_name="Bob", last_name="Foo",
                         pin_hash=User.salt_hash_secret('0000'))
    create_transfer_account_for_user(sender, token, 400)

    recipient = UserFactory(preferred_language="sw", phone=make_kenyan_phone(phone()), first_name="Joe", last_name="Bar")
    create_transfer_account_for_user(recipient, token, 200)

    messages = []
    session_id = 'ATUid_05af06225e6163ec2dc9dc9cf8bc97aa'

    def mock_send_message(phone, message):
        messages.append({'phone': phone, 'message': message})
    mocker.patch('server.message_processor.send_message', mock_send_message)

    def req(text):
        response = test_client.post(
            '/api/v1/ussd/kenya',
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

    resp = req("1")
    assert "CON Please enter your PIN" in resp

    resp = req("0000")
    assert "CON Send 12.5 SM1" in resp

    resp = req("1")
    assert "END Your request has been sent." in resp

    assert default_transfer_account(sender).balance == 387.5
    assert default_transfer_account(recipient).balance == 212.5

    assert len(messages) == 2
    sent_message = messages[0]
    assert sent_message['phone'] == sender.phone
    assert f"sent a payment of 12.5 SM1 to {recipient.first_name}" in sent_message['message']
    received_message = messages[1]
    assert received_message['phone'] == recipient.phone
    assert f"Umepokea 12.5 SM1 kutoka kwa {sender.first_name}" in received_message['message']

