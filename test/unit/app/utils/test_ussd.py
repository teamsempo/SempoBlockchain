import pytest
from functools import partial

from server import db
from fixtures.user import UserFactory
from server.models.ussd import UssdMenu, UssdSession
from server.utils.ussd.ussd import menu_display_text_in_lang, create_or_update_session


@pytest.mark.parametrize("user_factory,expected", [
    (None, "foo"),
    (partial(UserFactory), "foo"),
    (partial(UserFactory, preferred_language="en"), "foo"),
    (partial(UserFactory, preferred_language="sw_KE"), "bar"),
])
def test_menu_display_text_in_lang(test_client, init_database, user_factory, expected):
    user = user_factory() if user_factory else None

    menu = UssdMenu(display_text_en="foo", display_text_sw="bar")
    assert menu_display_text_in_lang(menu, user) == expected


def test_create_or_update_session(test_client, init_database):
    user = UserFactory(phone="123")

    # create a session in db
    session = UssdSession(session_id="1", user_id=user.id, msisdn="123", ussd_menu_id=3, state="foo", service_code="*123#")
    db.session.add(session)
    db.session.commit()

    # test updating existing
    create_or_update_session("1", user, UssdMenu(id=4, name="bar"), "input", "*123#")
    sessions = UssdSession.query.filter_by(session_id="1")
    assert sessions.count() == 1
    session = sessions.first()
    assert session.state == "bar"
    assert session.user_input == "input"
    assert session.ussd_menu_id == 4

    # test creating a new one
    sessions = UssdSession.query.filter_by(session_id="2")
    assert sessions.count() == 0
    create_or_update_session("2", user, UssdMenu(id=5, name="bat"), "", "*123#")
    sessions = UssdSession.query.filter_by(session_id="2")
    assert sessions.count() == 1
    session = sessions.first()
    assert session.state == "bat"
    assert session.user_input == ""
    assert session.ussd_menu_id == 5