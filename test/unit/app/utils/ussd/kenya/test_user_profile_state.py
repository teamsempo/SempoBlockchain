import json
import pytest
from functools import partial
from faker.providers import phone_number
from faker import Faker

from helpers.factories import UserFactory, UssdSessionFactory, OrganisationFactory
from server.utils.ussd.kenya_ussd_state_machine import KenyaUssdStateMachine
from server.models.user import User

fake = Faker()
fake.add_provider(phone_number)
phone = partial(fake.msisdn)

empty_profile_user = partial(UserFactory,
                             pin_hash=User.salt_hash_secret('0000'),
                             failed_pin_attempts=0,
                             preferred_language='en')

last_name_entry_state = partial(UssdSessionFactory, state='last_name_entry')
gender_entry_state = partial(UssdSessionFactory, state='gender_entry')
location_entry_state = partial(UssdSessionFactory, state='location_entry')
change_my_business_prompt_state = partial(UssdSessionFactory, state='change_my_business_prompt')


@pytest.mark.parametrize('session_factory, user_factory, user_input, expected_first_name, expected_last_name, '
                         'expected_state',
 [
     (last_name_entry_state, empty_profile_user, 'Bar', 'Foo', 'Bar', 'gender_entry')
 ])
def test_name_change(test_client, init_database, session_factory, user_factory, user_input, expected_first_name,
                     expected_last_name, expected_state):
    from flask import g
    g.active_organisation = OrganisationFactory(country_code='KE')

    session = session_factory()
    user = user_factory()
    user.phone = phone()

    session.session_data = {
        'first_name': 'Foo'
    }

    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.feed_char(user_input)
    assert state_machine.state == expected_state
    assert session.get_data('first_name') == expected_first_name
    assert session.get_data('last_name') == expected_last_name


@pytest.mark.parametrize('session_factory, user_factory, user_input, expected_state',
 [
     (gender_entry_state, empty_profile_user, '1', 'location_entry')
 ])
def test_gender_change(test_client, init_database, session_factory, user_factory, user_input, expected_state):
    session = session_factory()
    user = user_factory()
    user.phone = phone()

    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.feed_char(user_input)
    assert state_machine.state == expected_state


@pytest.mark.parametrize('session_factory, user_factory, user_input, expected',
 [
     (location_entry_state, empty_profile_user, 'Kibera', 'change_my_business_prompt')
 ])
def test_location_change(test_client, init_database, session_factory, user_factory, user_input, expected):
    session = session_factory()
    user = user_factory()
    user.phone = phone()

    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.feed_char(user_input)
    assert state_machine.state == expected
    assert session.get_data('location') == user_input


@pytest.mark.parametrize('session_factory, user_factory, user_input, expected',
 [
     (change_my_business_prompt_state, empty_profile_user, 'Kibera', 'profile_info_change_pin_authorization')
 ])
def test_save_directory_info(mocker, test_client, init_database, session_factory, user_factory, user_input, expected):
    session = UssdSessionFactory(state="change_my_business_prompt")
    user = user_factory()
    user.phone = phone()
    assert next(filter(lambda x: x.name == 'bio', user.custom_attributes), None) is None
    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.send_sms = mocker.MagicMock()

    state_machine.feed_char("My Bio")
    assert state_machine.state == expected
    session.session_data = {
        'bio': "My Bio"
    }
    state_machine.feed_char("0000")
    bio = next(filter(lambda x: x.name == 'bio', user.custom_attributes), None)
    assert bio.value == "My Bio"
