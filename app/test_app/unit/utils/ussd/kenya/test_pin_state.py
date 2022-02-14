import pytest
from functools import partial
from faker.providers import phone_number
from faker import Faker
import json

from helpers.model_factories import UserFactory, UssdSessionFactory, OrganisationFactory
from server.utils.ussd.ussd_state_machine import UssdStateMachine
from server.models.user import User

fake = Faker()
fake.add_provider(phone_number)
# why do i get dupes if i put it directly on standard_user...?
phone = partial(fake.msisdn)

base_user = partial(UserFactory, phone='+61400000000')
unactivated_user = partial(base_user, is_activated=False)
standard_user = partial(base_user, pin_hash=User.salt_hash_secret('0000'), failed_pin_attempts=0)
pin_blocked_user = partial(base_user, pin_hash=User.salt_hash_secret('0000'), failed_pin_attempts=3)

initial_pin_entry_state = partial(UssdSessionFactory, state="initial_pin_entry")
initial_pin_confirmation_state = partial(UssdSessionFactory, state="initial_pin_confirmation",
                                         session_data=json.loads('{"initial_pin": "0000"}'))
send_token_pin_authorization_state = partial(UssdSessionFactory, state="send_token_pin_authorization")
current_pin_state = partial(UssdSessionFactory, state="current_pin")
new_pin_state = partial(UssdSessionFactory, state="new_pin")
new_pin_confirmation_state = partial(UssdSessionFactory, state="new_pin_confirmation",
                                     session_data=json.loads('{"initial_pin": "2222"}'))
opt_out_of_market_place_pin_authorization_state = partial(UssdSessionFactory,
                                                          state="opt_out_of_market_place_pin_authorization")
exchange_token_pin_authorization_state = partial(UssdSessionFactory, state="exchange_token_pin_authorization")
exchange_rate_pin_authorization_state = partial(UssdSessionFactory, state="exchange_rate_pin_authorization")
balance_inquiry_pin_authorization_state = partial(UssdSessionFactory, state="balance_inquiry_pin_authorization")


@pytest.mark.parametrize("session_factory, user_factory, user_input, expected",
 [
     # initial_pin_entry transitions tests
     (initial_pin_entry_state, standard_user, "0000", "initial_pin_confirmation"),
     (initial_pin_entry_state, standard_user, "AAAA", "exit_invalid_pin"),
     # current_pin state tests
     (current_pin_state, standard_user, "0000", "new_pin"),
     (current_pin_state, pin_blocked_user, "1111", "exit_pin_blocked"),
     # new_pin state tests
     (new_pin_state, standard_user, "2222", "new_pin_confirmation"),
     (new_pin_state, standard_user, "0000", "exit_invalid_pin"),
     # new_pin_confirmation state tests
     (new_pin_confirmation_state, standard_user, "2222", "complete"),
     (new_pin_confirmation_state, standard_user, "1212", "exit_pin_mismatch"),
     # opt_out_of_market_place_pin_authorization state tests
     (opt_out_of_market_place_pin_authorization_state, pin_blocked_user, "1111",
      "exit_pin_blocked")
 ])
def test_kenya_state_machine(test_client, init_database, user_factory, session_factory, user_input, expected):
    from flask import g
    g.active_organisation = OrganisationFactory(country_code='AU')

    session = session_factory()
    user = user_factory()
    user.phone = phone()
    state_machine = UssdStateMachine(session, user)

    state_machine.feed_char(user_input)
    assert state_machine.state == expected


@pytest.mark.parametrize("session_factory, user_factory, user_input, expected, before_failed_pin_attempts, after_failed_pin_attempts",
 [
     # send token pin auth combinations
     (send_token_pin_authorization_state, pin_blocked_user, "1212", "exit_pin_blocked", 3, 3),
     (send_token_pin_authorization_state, standard_user, "1212",
      "send_token_pin_authorization", 1, 2),
     (send_token_pin_authorization_state, standard_user, "0000",
      "send_token_confirmation", 1, 0),
     (send_token_pin_authorization_state, standard_user, "1212",
      "exit_pin_blocked", 2, 3),
     (send_token_pin_authorization_state, standard_user, "0000",
      "send_token_confirmation", 2, 0),
     # balance inquiry pin auth combinations
     (balance_inquiry_pin_authorization_state, pin_blocked_user, "1212", "exit_pin_blocked", 3, 3),
     (balance_inquiry_pin_authorization_state, standard_user, "1212",
      "balance_inquiry_pin_authorization", 1, 2),
     (balance_inquiry_pin_authorization_state, standard_user, "0000",
      "complete", 1, 0),
     (balance_inquiry_pin_authorization_state, standard_user, "1212",
      "exit_pin_blocked", 2, 3),
     (balance_inquiry_pin_authorization_state, standard_user, "0000",
      "complete", 2, 0),
     # exchange token pin auth combinations
     (exchange_token_pin_authorization_state, pin_blocked_user, "1111", "exit_pin_blocked", 3, 3),
     (exchange_token_pin_authorization_state, standard_user, "1212",
      "exchange_token_pin_authorization", 1, 2),
     (exchange_token_pin_authorization_state, standard_user, "0000",
      "exchange_token_confirmation", 1, 0),
     (exchange_token_pin_authorization_state, standard_user, "1212",
      "exit_pin_blocked", 2, 3),
     (exchange_token_pin_authorization_state, standard_user, "0000",
      "exchange_token_confirmation", 2, 0),
     # exchange rate pin auth combinations
     (exchange_rate_pin_authorization_state, pin_blocked_user, "1111", "exit_pin_blocked", 3, 3),
     (exchange_rate_pin_authorization_state, standard_user, "1212",
      "exchange_rate_pin_authorization", 1, 2),
     (exchange_rate_pin_authorization_state, standard_user, "0000",
      "complete", 1, 0),
     (exchange_rate_pin_authorization_state, standard_user, "1212",
      "exit_pin_blocked", 2, 3),
     (exchange_rate_pin_authorization_state, standard_user, "0000",
      "complete", 2, 0),
 ])
def test_authorize_pin(test_client, init_database, session_factory, user_factory, user_input, expected,
                       before_failed_pin_attempts, after_failed_pin_attempts):
    session = session_factory()
    user = user_factory(phone='+6140000000')
    user.failed_pin_attempts = before_failed_pin_attempts

    state_machine = UssdStateMachine(session, user)

    state_machine.feed_char(user_input)
    assert state_machine.state == expected
    assert user.failed_pin_attempts == after_failed_pin_attempts


def test_change_initial_pin(mocker, test_client, init_database):
    session = initial_pin_confirmation_state()
    user = unactivated_user()

    state_machine = UssdStateMachine(session, user)

    assert user.pin_hash is None
    assert user.is_activated is False
    assert not user.is_phone_verified

    state_machine.feed_char("0000")

    assert user.verify_pin("0000") is True
    assert user.is_activated is True
    assert user.is_phone_verified



def test_change_current_pin(mocker, test_client, init_database):
    session = new_pin_confirmation_state()
    user = standard_user()

    state_machine = UssdStateMachine(session, user)
    state_machine.send_sms = mocker.MagicMock()

    state_machine.feed_char("2222")

    assert user.verify_pin("2222") is True
    state_machine.send_sms.assert_called_with(user.phone, "pin_change_success_sms")

# TODO: test pin confirmation failed + blocked + reset flow?
