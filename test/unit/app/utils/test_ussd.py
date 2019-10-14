import pytest

from server import db
from fixtures.user import UserFactory
from server.models.ussd import UssdMenu, UssdSession


@pytest.fixture(scope='function')
def menu_display_text_in_lang(test_client, init_database):
    from server.utils.ussd.ussd import menu_display_text_in_lang
    return menu_display_text_in_lang


@pytest.fixture(scope='function')
def create_or_update_session(test_client, init_database):
    from server.utils.ussd.ussd import create_or_update_session
    return create_or_update_session


# TODO(ussd): once preferred_language is added, add another test that sw_KE works and user without preferred_language
@pytest.mark.parametrize("case,expected", [
    (1, "foo"),
    (2, "foo"),
])
def test_menu_display_text_in_lang(menu_display_text_in_lang, case, expected):
    if case == 1:
        user = None
    else:
        # TODO: this is really gross, but I can't use the factory in the parameters since no db initiated... how do?
        user = UserFactory()

    menu = UssdMenu(display_text_en="foo", display_text_sw="bar")
    assert menu_display_text_in_lang(menu, user) == expected


def test_create_or_update_session(create_or_update_session):
    # create a session in db
    session = UssdSession(session_id="1", user_id=2, msisdn="123", ussd_menu_id=3, state="foo", service_code="*123#")
    db.session.add(session)
    db.session.commit()

    # test updating existing
    user = UserFactory(id=2, phone="123")
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
