import pytest
from functools import partial
from faker.providers import phone_number
from faker import Faker

from helpers.model_factories import UserFactory, UssdSessionFactory, OrganisationFactory
from helpers.utils import fake_transfer_mapping
from server import db
from server.utils.ussd.kenya_ussd_state_machine import KenyaUssdStateMachine
from server.models.user import User
from server.models.transfer_usage import TransferUsage

fake = Faker()
fake.add_provider(phone_number)
# why do i get dupes if i put it directly on standard_user...?
phone = partial(fake.msisdn)

standard_user = partial(UserFactory, pin_hash=User.salt_hash_secret('0000'), failed_pin_attempts=0)

initial_language_selection_state = partial(UssdSessionFactory, state="initial_language_selection")
start_state = partial(UssdSessionFactory, state="start")
account_management_state = partial(UssdSessionFactory, state="account_management")
my_business_state = partial(UssdSessionFactory, state="my_business")
choose_language_state = partial(UssdSessionFactory, state="choose_language")
directory_listing_state = partial(UssdSessionFactory, state="directory_listing")
directory_listing_other_state = partial(UssdSessionFactory, state="directory_listing_other")


@pytest.mark.parametrize("session_factory, user_factory, user_input, expected",
 [
     # initial_language_selection transitions tests
     (initial_language_selection_state, standard_user, "3", "help"),
     (initial_language_selection_state, standard_user, "5", "exit_invalid_menu_option"),
     (initial_language_selection_state, standard_user, "asdf", "exit_invalid_menu_option"),
     # start state transition tests
     (start_state, standard_user, "1", "send_enter_recipient"),
     (start_state, standard_user, "2", "account_management"),
     (start_state, standard_user, "3", "directory_listing"),
     (start_state, standard_user, "4", "exchange_token"),
     (start_state, standard_user, "5", "help"),
     (start_state, standard_user, "6", "exit_invalid_menu_option"),
     (start_state, standard_user, "asdf", "exit_invalid_menu_option"),
     # account_management state tests
     (account_management_state, standard_user, "1", "my_business"),
     (account_management_state, standard_user, "2", "choose_language"),
     (account_management_state, standard_user, "3", "balance_inquiry_pin_authorization"),
     (account_management_state, standard_user, "4", "current_pin"),
     (account_management_state, standard_user, "5", "opt_out_of_market_place_pin_authorization"),
     (account_management_state, standard_user, "6", "exit_invalid_menu_option"),
     (account_management_state, standard_user, "asdf", "exit_invalid_menu_option"),
     # my_business state tests
     (my_business_state, standard_user, "1", "about_my_business"),
     (my_business_state, standard_user, "2", "change_my_business_prompt"),
     (my_business_state, standard_user, "3", "exit_invalid_menu_option"),
     (my_business_state, standard_user, "asdf", "exit_invalid_menu_option"),
     # directory listing state tests
     (directory_listing_state, standard_user, "9", "directory_listing_other"),
     (directory_listing_state, standard_user, "1", "complete"),
     (directory_listing_state, standard_user, "10", "exit_invalid_menu_option"),
     (directory_listing_state, standard_user, "11", "exit_invalid_menu_option"),
     (directory_listing_state, standard_user, "asdf", "exit_invalid_menu_option"),
     # directory listing other state tests
     (directory_listing_other_state, standard_user, "1", "complete"),
     (directory_listing_other_state, standard_user, "9", "directory_listing_other"),
     (directory_listing_other_state, standard_user, "10", "directory_listing_other"),
     (directory_listing_other_state, standard_user, "11", "exit_invalid_menu_option"),
     (directory_listing_other_state, standard_user, "asdf", "exit_invalid_menu_option"),
     # choose_language state tests
     (choose_language_state, standard_user, "5", "exit_invalid_menu_option"),
     (choose_language_state, standard_user, "asdf", "exit_invalid_menu_option"),
 ])
def test_kenya_state_machine(test_client, init_database, user_factory, session_factory, user_input, expected):
    from flask import g
    g.active_organisation = OrganisationFactory(country_code='AU')

    session = session_factory()
    session.session_data = {
        'transfer_usage_mapping': fake_transfer_mapping(10),
        'usage_menu': 1,
        'usage_index_stack': [0, 8]
    }
    user = user_factory()
    user.phone = phone()
    db.session.commit()
    state_machine = KenyaUssdStateMachine(session, user)

    state_machine.feed_char(user_input)
    assert state_machine.state == expected


@pytest.mark.parametrize("session_factory, user_input, language", [
    (initial_language_selection_state, "1", "en"),
    (initial_language_selection_state, "2", "sw"),
])
def test_change_language_initial(mocker, test_client, init_database, session_factory, user_input, language):
    session = session_factory()
    user = standard_user()
    assert user.preferred_language is None

    state_machine = KenyaUssdStateMachine(session, user)

    state_machine.feed_char(user_input)
    assert state_machine.state == "initial_pin_entry"
    assert user.preferred_language == language

@pytest.mark.parametrize("session_factory, user_input, language", [
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
    state_machine.send_sms.assert_called_with(user.phone, "language_change_sms")


def test_opt_out_of_marketplace(mocker, test_client, init_database):
    session = UssdSessionFactory(state="opt_out_of_market_place_pin_authorization")
    user = standard_user()
    user.phone = phone()
    assert next(filter(lambda x: x.key == 'market_enabled', user.custom_attributes), None) is None
    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.send_sms = mocker.MagicMock()

    state_machine.feed_char("0000")
    assert state_machine.state == "complete"
    assert user.is_market_enabled == False
    state_machine.send_sms.assert_called_with(user.phone, "opt_out_of_market_place_sms")


def test_save_directory_info(mocker, test_client, init_database):
    session = UssdSessionFactory(state="change_my_business_prompt")
    user = standard_user()
    user.phone = phone()
    assert next(filter(lambda x: x.key == 'bio', user.custom_attributes), None) is None
    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.send_sms = mocker.MagicMock()

    state_machine.feed_char("My Bio")
    assert state_machine.state == "exit"
    bio = next(filter(lambda x: x.key == 'bio', user.custom_attributes), None)
    assert bio.value == "My Bio"


def test_balance_inquiry(mocker, test_client, init_database):
    session = UssdSessionFactory(state="balance_inquiry_pin_authorization")
    user = standard_user()
    user.phone = phone()

    state_machine = KenyaUssdStateMachine(session, user)
    inquire_balance = mocker.MagicMock()
    mocker.patch('server.ussd_tasker.inquire_balance', inquire_balance)

    state_machine.feed_char('0000')
    assert state_machine.state == 'complete'
    inquire_balance.assert_called_with(user)


def test_send_directory_listing(mocker, test_client, init_database):
    session = UssdSessionFactory(state="directory_listing")
    session.session_data = {'transfer_usage_mapping': fake_transfer_mapping(6), 'usage_menu': 0}
    user = standard_user()
    user.phone = phone()
    state_machine = KenyaUssdStateMachine(session, user)
    transfer_usage = TransferUsage.find_or_create("Food")

    send_directory_listing = mocker.MagicMock()
    mocker.patch('server.ussd_tasker.send_directory_listing', send_directory_listing)

    state_machine.feed_char('2')
    assert state_machine.state == 'complete'
    send_directory_listing.assert_called_with(user, transfer_usage)


def test_terms_only_sent_once(mocker, test_client, init_database, mock_sms_apis):
    session = UssdSessionFactory(state="balance_inquiry_pin_authorization")
    user = standard_user()
    user.phone = phone()

    inquire_balance = mocker.MagicMock()
    mocker.patch('server.ussd_tasker.inquire_balance', inquire_balance)

    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.feed_char('0000')

    db.session.commit()

    messages = mock_sms_apis

    assert len(messages) == 1

    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.feed_char('0000')

    assert len(messages) == 1


