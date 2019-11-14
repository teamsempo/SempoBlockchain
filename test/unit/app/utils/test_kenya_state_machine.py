import pytest
from functools import partial
from faker.providers import phone_number
from faker import Faker

from helpers.user import UserFactory
from helpers.ussd_session import UssdSessionFactory
from server.utils.ussd.kenya_ussd_state_machine import KenyaUssdStateMachine
from server.models.user import User

fake = Faker()
fake.add_provider(phone_number)
# why do i get dupes if i put it directly on standard_user...?
phone = partial(fake.msisdn)

unactivated_user = partial(UserFactory, is_activated=False)
standard_user = partial(UserFactory, pin_hash=User.salt_hash_secret('0000'), failed_pin_attempts=0)
two_failed_pin_attempts_user = partial(UserFactory, pin_hash=User.salt_hash_secret('0000'), failed_pin_attempts=2)
one_failed_pin_attempts_user = partial(UserFactory, pin_hash=User.salt_hash_secret('0000'), failed_pin_attempts=1)
pin_blocked_user = partial(UserFactory, pin_hash=User.salt_hash_secret('0000'), failed_pin_attempts=3)
# TODO: [Philip] Find out how token agents are stored
token_agent = partial(UserFactory, held_roles={"TOKEN_AGENT": "grassroots_token_agent"})

initial_language_selection_state = partial(UssdSessionFactory, state="initial_language_selection")
initial_pin_entry_state = partial(UssdSessionFactory, state="initial_pin_entry")
initial_pin_confirmation_state = partial(UssdSessionFactory, state="initial_pin_confirmation", user_input="0000*0000")
start_state = partial(UssdSessionFactory, state="start")
send_enter_recipient_state = partial(UssdSessionFactory, state="send_enter_recipient")
send_token_amount_state = partial(UssdSessionFactory, state="send_token_amount")
send_token_reason_state = partial(UssdSessionFactory, state="send_token_reason")
send_token_reason_other_state = partial(UssdSessionFactory, state="send_token_reason_other")
send_token_pin_authorization_state = partial(UssdSessionFactory, state="send_token_pin_authorization")
send_token_confirmation_state = partial(UssdSessionFactory, state="send_token_confirmation")
account_management_state = partial(UssdSessionFactory, state="account_management")
my_business_state = partial(UssdSessionFactory, state="my_business")
choose_language_state = partial(UssdSessionFactory, state="choose_language")

balance_inquiry_pin_authorization_state = partial(UssdSessionFactory, state="balance_inquiry_pin_authorization")
current_pin_state = partial(UssdSessionFactory, state="current_pin")
new_pin_state = partial(UssdSessionFactory, state="new_pin")
new_pin_confirmation_state = partial(UssdSessionFactory, state="new_pin_confirmation", user_input="2222*2222")
opt_out_of_market_place_pin_authorization_state = partial(UssdSessionFactory, state="opt_out_of_market_place_pin_authorization")
exchange_token_state = partial(UssdSessionFactory, state="exchange_token")
exchange_rate_pin_authorization_state = partial(UssdSessionFactory, state="exchange_rate_pin_authorization")
exchange_token_agent_number_entry_transitions_state = partial(UssdSessionFactory,
                                                              state="exchange_token_agent_number_entry_transitions")
exchange_token_amount_entry_state = partial(UssdSessionFactory, state="exchange_token_amount_entry")
exchange_token_pin_authorization_state = partial(UssdSessionFactory, state="exchange_token_pin_authorization")
exchange_token_confirmation_state = partial(UssdSessionFactory, state="exchange_token_confirmation")


@pytest.mark.parametrize("session_factory, user_factory, user_input, expected",
 [
     # initial_language_selection transitions tests
     (initial_language_selection_state, standard_user, "3", "help"),
     (initial_language_selection_state, standard_user, "5", "exit_invalid_menu_option"),
     # initial_pin_entry transitions tests
     (initial_pin_entry_state, standard_user, "0000", "initial_pin_confirmation"),
     (initial_pin_entry_state, standard_user, "AAAA", "exit_invalid_pin"),
     # initial_pin_confirmation transitions tests
     (initial_pin_confirmation_state, standard_user, "0000", "complete"),
     (initial_pin_confirmation_state, standard_user, "1212", "exit_pin_mismatch"),
     # start state transition tests
     (start_state, standard_user, "1", "send_enter_recipient"),
     (start_state, standard_user, "2", "account_management"),
     (start_state, standard_user, "3", "directory_listing"),
     (start_state, standard_user, "4", "exchange_token"),
     (start_state, standard_user, "5", "help"),
     (start_state, standard_user, "6", "exit_invalid_menu_option"),
     # send_enter_recipient state tests
     # TODO: (send_enter_recipient_state, standard_user, "0712345678", "send_token_amount"),
     # TODO: (send_enter_recipient_state, token_agent, "0712345678", "exit_use_exchange_menu")
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
     (send_token_pin_authorization_state, pin_blocked_user, "1111", "exit_pin_blocked"),
     # send_token_confirmation state tests
     (send_token_confirmation_state, standard_user, "1", "complete"),
     (send_token_confirmation_state, standard_user, "2", "exit"),
     (send_token_confirmation_state, standard_user, "3", "exit_invalid_menu_option"),
     # account_management state tests
     (account_management_state, standard_user, "1", "my_business"),
     (account_management_state, standard_user, "2", "choose_language"),
     (account_management_state, standard_user, "3", "balance_inquiry_pin_authorization"),
     (account_management_state, standard_user, "4", "current_pin"),
     (account_management_state, standard_user, "5", "opt_out_of_market_place_pin_authorization"),
     (account_management_state, standard_user, "6", "exit_invalid_menu_option"),
     # my_business state tests
     (my_business_state, standard_user, "1", "about_my_business"),
     (my_business_state, standard_user, "2", "change_my_business_prompt"),
     # choose_language state tests
     (choose_language_state, standard_user, "5", "exit_invalid_menu_option"),
     # balance_inquiry_pin_authorization state tests
     (balance_inquiry_pin_authorization_state, standard_user, "0000", "complete"),
     (balance_inquiry_pin_authorization_state, pin_blocked_user, "1111",
      "exit_pin_blocked"),
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
      "exit_pin_blocked"),
     # exchange_token state tests
     (exchange_token_state, standard_user, "1", "exchange_rate_pin_authorization"),
     (exchange_token_state, standard_user, "2", "exchange_token_agent_number_entry"),
     (exchange_token_state, standard_user, "3", "exit_invalid_menu_option"),
     # exchange_rate_pin_authorization state tests
     (exchange_rate_pin_authorization_state, standard_user, "0000", "complete"),
     (exchange_rate_pin_authorization_state, pin_blocked_user, "1111",
      "exit_pin_blocked"),
     # exchange_token_agent_number_entry state tests
     # TODO: (exchange_token_agent_number_entry_transitions_state, standard_user, "0712345678", "exchange_token_amount_entry"),
     # TODO: (exchange_token_agent_number_entry_transitions_state, standard_user, "0701010101", "exit_invalid_token_agent"),
     # exchange_token_amount_entry state tests
     (exchange_token_amount_entry_state, standard_user, "40",
      "exchange_token_pin_authorization"),
     (exchange_token_amount_entry_state, standard_user, "25", "exit_invalid_exchange_amount"),
     # exchange_token_pin_authorization state tests
     (exchange_token_pin_authorization_state, standard_user, "0000",
      "exchange_token_confirmation"),
     (exchange_token_pin_authorization_state, pin_blocked_user, "1111",
      "exit_pin_blocked"),
     # exchange_token_confirmation state tests
     (exchange_token_confirmation_state, standard_user, "1", "complete"),
     (exchange_token_confirmation_state, standard_user, "2", "exit"),
     (exchange_token_confirmation_state, standard_user, "3", "exit_invalid_menu_option")
 ])
def test_kenya_state_machine(test_client, init_database, user_factory, session_factory, user_input, expected):
    session = session_factory()
    user = user_factory()
    user.phone = phone()
    state_machine = KenyaUssdStateMachine(session, user)

    state_machine.feed_char(user_input)
    assert state_machine.state == expected


@pytest.mark.parametrize("session_factory, user_input, language", [
    (initial_language_selection_state, "1", "en"),
    (initial_language_selection_state, "2", "sw"),
    (choose_language_state, "1", "en"),
    (choose_language_state, "2", "sw"),
])
def test_change_language(mocker, test_client, init_database, session_factory, user_input, language):
    session = session_factory()
    user = standard_user()
    user.phone = phone()
    assert user.preferred_language is None

    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.send_sms = mocker.MagicMock()

    state_machine.feed_char(user_input)
    assert state_machine.state == "complete"
    assert user.preferred_language == language
    state_machine.send_sms.assert_called_with("language_change_sms")


# TODO: need pin authorisation implemented to do this
def test_opt_out_of_marketplace(mocker, test_client, init_database):
    session = opt_out_of_market_place_pin_authorization_state()
    user = standard_user()
    user.phone = phone()
    #TODO: how fetch from custom attributes?
    #assert user.custom_attributes['market_enabled'] == None
    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.send_sms = mocker.MagicMock()

    state_machine.feed_char("0000")
    assert state_machine.state == "complete"
    #assert user.custom_attributes['market_enabled'] == False
    state_machine.send_sms.assert_called_with("opt_out_of_market_place_sms")


@pytest.mark.parametrize("session_factory, user_input, expected, failed_pin_attempts", [
    (send_token_pin_authorization_state, "1212", "send_token_pin_authorization", 1),

])
def test_authorize_pin(test_client, init_database, session_factory, user_input, expected, failed_pin_attempts):
    session = session_factory()
    user = standard_user()
    assert user.failed_pin_attempts == 0

    state_machine = KenyaUssdStateMachine(session, user)

    state_machine.feed_char(user_input)
    assert state_machine.state == expected
    assert user.failed_pin_attempts == failed_pin_attempts


@pytest.mark.parametrize("session_factory, user_factory, user_input, expected, failed_pin_attempts", [
    (send_token_pin_authorization_state, pin_blocked_user, "1212", "exit_pin_blocked", 3),
    (send_token_pin_authorization_state, one_failed_pin_attempts_user, "1212", "send_token_pin_authorization", 2),
    (send_token_pin_authorization_state, one_failed_pin_attempts_user, "0000", "send_token_confirmation", 0),
    (send_token_pin_authorization_state, two_failed_pin_attempts_user, "1212", "exit_pin_blocked", 3),
    (send_token_pin_authorization_state, two_failed_pin_attempts_user, "0000", "send_token_confirmation", 0)
])
def test_exit_pin_blocked(test_client, init_database, session_factory, user_factory, user_input, expected, failed_pin_attempts):
    session = session_factory()
    user = user_factory()

    state_machine = KenyaUssdStateMachine(session, user)

    state_machine.feed_char(user_input)
    assert state_machine.state == expected
    assert user.failed_pin_attempts == failed_pin_attempts
