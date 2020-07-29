import pytest
from functools import partial
from faker.providers import phone_number
from faker import Faker
import json
from server import db

from helpers.model_factories import UserFactory, UssdSessionFactory, OrganisationFactory
from helpers.utils import make_kenyan_phone
from server.utils.ussd.kenya_ussd_state_machine import KenyaUssdStateMachine
from server.models.user import User

fake = Faker()
fake.add_provider(phone_number)
# why do i get dupes if i put it directly on standard_user...?
phone = partial(fake.msisdn)

standard_user = partial(UserFactory, pin_hash=User.salt_hash_secret('0000'), failed_pin_attempts=0)

exchange_token_state = partial(UssdSessionFactory, state="exchange_token")
directory_listing_state = partial(UssdSessionFactory, state="directory_listing")
exchange_rate_pin_authorization_state = partial(UssdSessionFactory, state="exchange_rate_pin_authorization")
exchange_token_agent_number_entry_state = partial(UssdSessionFactory,
                                                              state="exchange_token_agent_number_entry")
exchange_token_amount_entry_state = partial(UssdSessionFactory, state="exchange_token_amount_entry")
exchange_token_pin_authorization_state = partial(UssdSessionFactory, state="exchange_token_pin_authorization")
exchange_token_confirmation_state = partial(UssdSessionFactory, state="exchange_token_confirmation")


@pytest.mark.parametrize("session_factory, user_factory, user_input, expected",
 [
     # exchange_token state tests
     (exchange_token_state, standard_user, "1", "complete"),
     (exchange_token_state, standard_user, "2", "exchange_token_agent_number_entry"),
     (exchange_token_state, standard_user, "3", "exit_invalid_menu_option"),
     (exchange_token_state, standard_user, "asdf", "exit_invalid_menu_option"),
     # exchange_token_amount_entry state tests
     (exchange_token_amount_entry_state, standard_user, "2", "exchange_token_pin_authorization"),
     (exchange_token_amount_entry_state, standard_user, "40", "exchange_token_pin_authorization"),
     (exchange_token_amount_entry_state, standard_user, "0.01", "exit_invalid_exchange_amount"),
     (exchange_token_amount_entry_state, standard_user, "-1", "exit_invalid_exchange_amount"),
     (exchange_token_amount_entry_state, standard_user, "asdf", "exit_invalid_exchange_amount"),
     # exchange_token_pin_authorization state tests
     (exchange_token_pin_authorization_state, standard_user, "0000", "exchange_token_confirmation"),
     # exchange_token_confirmation state tests
     (exchange_token_confirmation_state, standard_user, "2", "exit"),
     (exchange_token_confirmation_state, standard_user, "3", "exit_invalid_menu_option"),
     (exchange_token_confirmation_state, standard_user, "asdf", "exit_invalid_menu_option"),
 ])
def test_kenya_state_machine(test_client, init_database, user_factory, session_factory, user_input, expected):
    from flask import g
    g.active_organisation = OrganisationFactory(country_code='AU')

    session = session_factory()
    user = user_factory()
    user.phone = phone()
    state_machine = KenyaUssdStateMachine(session, user)

    state_machine.feed_char(user_input)
    assert state_machine.state == expected

def test_invalid_user_recipient(test_client, init_database):
    session = exchange_token_agent_number_entry_state()
    user = standard_user()
    user.phone = phone()

    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.feed_char("1234")

    assert state_machine.state == "exit_invalid_token_agent"
    assert session.session_data is None


def test_user_recipient(test_client, init_database):
    session = exchange_token_agent_number_entry_state()
    user = standard_user()
    user.phone = phone()

    user_recipient = UserFactory(phone=make_kenyan_phone(phone()))

    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.feed_char(user_recipient.phone)

    assert state_machine.state == "exit_invalid_token_agent"
    assert session.session_data is None


def test_agent_recipient(test_client, init_database):
    session = exchange_token_agent_number_entry_state()
    user = standard_user()
    user.phone = phone()

    agent_recipient = UserFactory(phone=make_kenyan_phone(phone()))
    agent_recipient.set_held_role('TOKEN_AGENT', 'token_agent')

    state_machine = KenyaUssdStateMachine(session, user)
    state_machine.feed_char(agent_recipient.phone)

    assert state_machine.state == "exchange_token_amount_entry"
    assert session.get_data('agent_phone') == agent_recipient.phone


def test_exchange_token(mocker, test_client, init_database, create_transfer_account_user):
    agent_recipient = create_transfer_account_user
    agent_recipient.phone = make_kenyan_phone(agent_recipient.phone)
    agent_recipient.set_held_role('TOKEN_AGENT', 'token_agent')

    exchange_token_confirmation = UssdSessionFactory(
        state="exchange_token_confirmation",
        session_data=json.loads(
            "{" +
            f'"agent_phone": "{agent_recipient.phone}",'
            '"exchange_amount": "50"'
            + "}"
        )
    )

    user = standard_user()
    user.phone = phone()

    state_machine = KenyaUssdStateMachine(exchange_token_confirmation, user)
    exchange_token = mocker.MagicMock()
    mocker.patch('server.ussd_tasker.exchange_token', exchange_token)

    state_machine.feed_char("1")
    assert state_machine.state == "complete"
    exchange_token.assert_called_with(user, agent_recipient, 50)
