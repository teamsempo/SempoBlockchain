import pytest
from functools import partial

from fixtures.ussd_session import UssdSessionFactory
from server.utils.ussd.kenya_ussd_state_machine import KenyaUssdStateMachine


@pytest.mark.parametrize("session_factory,user_input,expected", [
    (partial(UssdSessionFactory,state="start"), "1", "send_enter_recipient"),
])
def test_kenya_state_machine(test_client, init_database, session_factory, user_input, expected):
    session = session_factory()
    state_machine = KenyaUssdStateMachine(session)

    state_machine.feed_char(user_input)
    assert state_machine.state == expected
