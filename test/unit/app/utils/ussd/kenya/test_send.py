import pytest
from functools import partial
from faker.providers import phone_number
from faker import Faker
import json

from helpers.user import UserFactory
from helpers.ussd_session import UssdSessionFactory
from server.utils.ussd.kenya_ussd_state_machine import KenyaUssdStateMachine
from server.models.user import User

fake = Faker()
fake.add_provider(phone_number)
# why do i get dupes if i put it directly on standard_user...?
phone = partial(fake.msisdn)

standard_user = partial(UserFactory, pin_hash=User.salt_hash_secret('0000'), failed_pin_attempts=0)

send_enter_recipient_state = partial(UssdSessionFactory, state="send_enter_recipient")
send_token_amount_state = partial(UssdSessionFactory, state="send_token_amount")
send_token_reason_state = partial(UssdSessionFactory, state="send_token_reason")
send_token_reason_other_state = partial(UssdSessionFactory, state="send_token_reason_other")
send_token_pin_authorization_state = partial(UssdSessionFactory, state="send_token_pin_authorization")
send_token_confirmation_state = partial(UssdSessionFactory, state="send_token_confirmation")


def make_kenyan_phone(phone_str):
    phone_list = list(phone_str)
    phone_list[0] = "6"
    phone_list[1] = "1"
    return ''.join(phone_list)


@pytest.mark.parametrize("session_factory, user_factory, user_input, expected",
 [
     # send_token_amount state test
     (send_token_amount_state, standard_user, "500", "send_token_reason"),
     # send_token_reasons state tests
     (send_token_reason_state, standard_user, "10", "send_token_reason_other"),
     (send_token_reason_state, standard_user, "5", "send_token_pin_authorization"),
     # send_token_reason_other state tests
     (send_token_reason_other_state, standard_user, "Some reason",
      "send_token_pin_authorization"),
     # send_token_pin_authorization state tests
     (send_token_pin_authorization_state, standard_user, "0000", "send_token_confirmation"),
     # send_token_confirmation state tests
     (send_token_confirmation_state, standard_user, "2", "exit"),
     (send_token_confirmation_state, standard_user, "3", "exit_invalid_menu_option"),
 ])
def test_kenya_state_machine(test_client, init_database, user_factory, session_factory, user_input, expected):
    session = session_factory()
    user = user_factory()
    user.phone = phone()
    state_machine = KenyaUssdStateMachine(session, user)

    state_machine.feed_char(user_input)
    assert state_machine.state == expected


def test_invalid_recipient(mocker, test_client, init_database, create_transfer_account_user, external_reserve_token):
    session = send_enter_recipient_state()
    user = standard_user()
    user.phone = phone()

    invalid_recipient = create_transfer_account_user
    invalid_recipient.is_disabled = True
    invalid_recipient.phone = make_kenyan_phone(invalid_recipient.phone)

    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.send_sms = mocker.MagicMock()
    state_machine.feed_char(invalid_recipient.phone)

    assert state_machine.state == "exit_invalid_recipient"
    assert session.session_data is None

    # implicitly tests default_token + couples it to organisation being external_reserve... could test better
    state_machine.send_sms.assert_called_with(
        invalid_recipient.phone,
        "upsell_message",
        first_name=invalid_recipient.first_name,
        last_name=invalid_recipient.last_name,
        community_token=external_reserve_token.name
    )


def test_standard_recipient(test_client, init_database):
    session = send_enter_recipient_state()
    user = standard_user()
    user.phone = phone()

    recipient_user = UserFactory(phone=make_kenyan_phone(phone()))

    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.feed_char(recipient_user.phone)

    assert state_machine.state == "send_token_amount"
    assert session.get_data('recipient_phone') == recipient_user.phone


def test_agent_recipient(test_client, init_database):
    session = send_enter_recipient_state()
    user = standard_user()
    user.phone = phone()

    agent_recipient = UserFactory(phone=make_kenyan_phone(phone()))
    agent_recipient.set_held_role('TOKEN_AGENT', 'grassroots_token_agent')

    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.feed_char(agent_recipient.phone)

    assert state_machine.state == "exit_use_exchange_menu"
    assert session.session_data is None


def test_send_token(mocker, test_client, init_database, create_transfer_account_user):
    recipient = create_transfer_account_user
    recipient.phone = make_kenyan_phone(recipient.phone)

    send_token_confirmation = UssdSessionFactory(
        state="send_token_confirmation",
        session_data=json.loads(
            "{" +
            f'"recipient_phone": "{recipient.phone}",'
            '"transaction_amount": "10",'
            '"transaction_reason_translated": "A reason",'
            '"transaction_reason_id": "1"'
            + "}"
        )
    )

    user = standard_user()
    user.phone = phone()

    state_machine = KenyaUssdStateMachine(send_token_confirmation, user)
    send_token = mocker.MagicMock()
    mocker.patch('server.ussd_tasker.send_token', send_token)

    state_machine.feed_char("1")
    assert state_machine.state == "complete"
    send_token.assert_called_with(user, recipient, 10, "A reason", 1)
