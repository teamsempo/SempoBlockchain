import pytest
from functools import partial

from server import db
from helpers.model_factories import UserFactory, OrganisationFactory
from server.models.ussd import UssdMenu, UssdSession
from server.utils.ussd.ussd import menu_display_text_in_lang, create_or_update_session


@pytest.mark.parametrize("user_factory,expected", [
    (partial(UserFactory, preferred_language="jp"), "END Invalid request"),
    (partial(UserFactory, preferred_language="sw"), "END Chaguo si sahihi"),
    (partial(UserFactory, preferred_language="en"), "END Invalid request"),
    (partial(UserFactory), "END Invalid request"),
    (None, "END Invalid request"),
])
def test_menu_display_text_in_lang(test_client, init_database, user_factory, expected):
    user = user_factory() if user_factory else None

    menu = UssdMenu(display_key="ussd.sempo.exit_invalid_request")
    result = menu_display_text_in_lang(menu, user)
    assert result == expected


def test_create_or_update_session(test_client, init_database):
    from flask import g
    g.active_organisation = OrganisationFactory(country_code='AU')

    user = UserFactory(phone="123")

    # create a session in db

    menu3 = UssdMenu(id=3, name='foo', display_key='foo')
    db.session.add(menu3)

    session = UssdSession(
        session_id="1", user_id=user.id, msisdn="123", ussd_menu=menu3, state="foo", service_code="*123#"
    )
    db.session.add(session)
    db.session.commit()

    # test updating existing
    create_or_update_session("1", user, UssdMenu(id=4, name="bar", display_key='bar'), "input", "*123#")
    sessions = UssdSession.query.filter_by(session_id="1")
    assert sessions.count() == 1
    session = sessions.first()
    assert session.state == "bar"
    assert session.user_input == "input"
    assert session.ussd_menu_id == 4

    # test creating a new one
    sessions = UssdSession.query.filter_by(session_id="2")
    assert sessions.count() == 0
    create_or_update_session("2", user, UssdMenu(id=5, name="bat", display_key='bat'), "", "*123#")
    sessions = UssdSession.query.filter_by(session_id="2")
    assert sessions.count() == 1
    session = sessions.first()
    assert session.state == "bat"
    assert session.user_input == ""
    assert session.ussd_menu_id == 5