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

standard_user = partial(UserFactory, pin_hash=User.salt_hash_secret('0000'),
                        failed_pin_attempts=0,
                        preferred_language='en')

first_name_entry_state = partial(UssdSessionFactory, state='first_name_entry')
last_name_entry_state = partial(UssdSessionFactory, state='last_name_entry',
                                session_data=json.loads('{"first_name": "Philip"}'))
gender_entry_state = partial(UssdSessionFactory, state='gender_entry')
location_entry_state = partial(UssdSessionFactory, state='location_entry')


@pytest.mark.parametrize('session_factory, user_factory, user_input, expected',
 [
     (last_name_entry_state, standard_user, 'Wafula', 'exit'),
 ])
def test_name_change(test_client, init_database, session_factory, user_factory, user_input, expected):
    from flask import g
    g.active_organisation = OrganisationFactory(country_code='KE')

    session = session_factory()
    user = user_factory()
    user.phone = phone()

    assert user.first_name is None
    assert user.last_name is None

    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.feed_char(user_input)

    assert user.first_name == 'Philip'
    assert user.last_name == 'Wafula'
    assert state_machine.state == expected


@pytest.mark.parametrize('session_factory, user_factory, user_input, expected',
 [
     (gender_entry_state, standard_user, '1', 'exit'),
 ])
def test_gender_change(test_client, init_database, session_factory, user_factory, user_input, expected):
    session = session_factory()
    user = user_factory()
    user.phone = phone()

    assert next(filter(lambda x: x.name == 'gender', user.custom_attributes), None) is None

    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.feed_char(user_input)

    gender = next(filter(lambda x: x.name == 'gender', user.custom_attributes), None)
    assert gender.value == 'Male'
    assert state_machine.state == expected


@pytest.mark.parametrize('session_factory, user_factory, user_input, expected',
 [
     (location_entry_state, standard_user, 'Kibera', 'exit'),
 ])
def test_location_change(test_client, init_database, session_factory, user_factory, user_input, expected):
    session = session_factory()
    user = user_factory(id=1)
    user.phone = phone()

    assert user.location is None

    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.feed_char(user_input)

    assert user.location == 'Kibera'
    assert state_machine.state == expected


def test_save_directory_info(mocker, test_client, init_database):
    session = UssdSessionFactory(state="change_my_business_prompt")
    user = standard_user()
    user.phone = phone()
    assert next(filter(lambda x: x.name == 'bio', user.custom_attributes), None) is None
    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.send_sms = mocker.MagicMock()

    state_machine.feed_char("My Bio")
    assert state_machine.state == "exit"
    bio = next(filter(lambda x: x.name == 'bio', user.custom_attributes), None)
    assert bio.value == "My Bio"
