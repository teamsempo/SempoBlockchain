import pytest
from functools import partial
from faker.providers import phone_number
from faker import Faker
import json

from helpers.factories import UserFactory, UssdSessionFactory, TokenFactory, OrganisationFactory
from helpers.ussd_utils import make_kenyan_phone, fake_transfer_mapping
from server import db
from server.utils.ussd.kenya_ussd_state_machine import KenyaUssdStateMachine
from server.models.user import User

fake = Faker()
fake.add_provider(phone_number)
# why do i get dupes if i put it directly on standard_user...?
phone = partial(fake.msisdn)

@pytest.fixture(scope='function')
def standard_user(test_client, init_database):
    from flask import g

    token = TokenFactory(name='Sarafu', symbol='SARAFU')
    organisation = OrganisationFactory(token=token, country_code='AU')
    g.active_organisation = organisation

    return UserFactory(
        first_name="Foo",
        last_name="Bar",
        pin_hash=User.salt_hash_secret('0000'),
        failed_pin_attempts=0,
        phone=phone(),
        default_organisation=organisation
    )


send_enter_recipient_state = partial(UssdSessionFactory, state="send_enter_recipient")
send_token_amount_state = partial(UssdSessionFactory, state="send_token_amount")
send_token_pin_authorization_state = partial(UssdSessionFactory, state="send_token_pin_authorization")


@pytest.mark.parametrize("session_factory, user_input, expected",
 [
     # send_token_amount state test
     (send_token_amount_state, "12.5", "send_token_pin_authorization"),
     (send_token_amount_state, "500", "send_token_pin_authorization"),
     (send_token_amount_state, "-1", "exit_invalid_input"),
     (send_token_amount_state, "asdf", "exit_invalid_input"),
 ])
def test_kenya_state_machine(test_client, init_database, standard_user, session_factory, user_input, expected):
    session = session_factory()
    session.session_data = {
        'transfer_usage_mapping': fake_transfer_mapping(10),
        'usage_menu': 1,
        'usage_index_stack': [0, 8],
    }
    db.session.commit()
    state_machine = KenyaUssdStateMachine(session, standard_user)

    state_machine.feed_char(user_input)
    assert state_machine.state == expected


def test_invalid_user_recipient(mocker, test_client, init_database, standard_user):
    session = send_enter_recipient_state()
    state_machine = KenyaUssdStateMachine(session, standard_user)
    state_machine.send_sms = mocker.MagicMock()
    state_machine.feed_char("1234")

    assert state_machine.state == "exit_invalid_recipient"
    assert session.session_data is None


def test_invalid_recipient(
        mocker, test_client, init_database, standard_user, create_transfer_account_user, external_reserve_token
):
    session = send_enter_recipient_state()

    invalid_recipient_phone = "+61234567890"

    state_machine = KenyaUssdStateMachine(session, standard_user)
    state_machine.send_sms = mocker.MagicMock()
    state_machine.feed_char(invalid_recipient_phone)

    assert state_machine.state == "exit_invalid_recipient"
    assert session.session_data is None

    state_machine.send_sms.assert_called_with(
        invalid_recipient_phone,
        "upsell_message_recipient",
        first_name=standard_user.first_name,
        last_name=standard_user.last_name,
        token_name=standard_user.default_organisation.token.name
    )


def test_standard_recipient(test_client, init_database, standard_user):
    session = send_enter_recipient_state()

    recipient_user = UserFactory(phone=make_kenyan_phone(phone()))

    state_machine = KenyaUssdStateMachine(session, standard_user)
    state_machine.feed_char(recipient_user.phone)

    assert state_machine.state == "send_token_amount"
    assert session.get_data('recipient_phone') == recipient_user.phone


def test_agent_recipient(test_client, init_database, standard_user):
    session = send_enter_recipient_state()

    agent_recipient = UserFactory(phone=make_kenyan_phone(phone()))
    agent_recipient.set_held_role('TOKEN_AGENT', 'grassroots_token_agent')

    state_machine = KenyaUssdStateMachine(session, standard_user)
    state_machine.feed_char(agent_recipient.phone)

    assert state_machine.state == "exit_use_exchange_menu"
    assert session.session_data is None


def test_send_token(mocker, test_client, init_database, create_transfer_account_user, standard_user):
    recipient = create_transfer_account_user
    recipient.phone = make_kenyan_phone(recipient.phone)

    send_token_pin_authorization = UssdSessionFactory(
        state="send_token_pin_authorization",
        session_data=json.loads(
            "{" +
            f'"recipient_phone": "{recipient.phone}",'
            '"transaction_amount": "10"'
            + "}"
        )
    )

    state_machine = KenyaUssdStateMachine(send_token_pin_authorization, standard_user)
    send_token = mocker.MagicMock()
    mocker.patch('server.ussd_tasker.send_token', send_token)

    state_machine.feed_char("0000")
    assert state_machine.state == "complete"
    send_token.assert_called_with(sender=standard_user, recipient=recipient, amount=10.0)
