from typing import Optional

from server import db
from server.models.user import User
from server.models.ussd import UssdMenu, UssdSession
from server.utils.internationalization import i18n_for


def menu_display_text_in_lang(current_menu: UssdMenu, user: Optional[User]) -> str:
    return i18n_for(user, current_menu.display_key)


def create_or_update_session(session_id: str, user: User, current_menu: UssdMenu, user_input: str, service_code: str) -> UssdSession:
    session: Optional[UssdSession] = UssdSession.query.filter_by(session_id=session_id).first()
    if session:
        session.user_input = user_input
        session.ussd_menu = current_menu
        session.state = current_menu.name
    else:
        session = UssdSession(session_id=session_id, msisdn=user.phone, user_input=user_input,
                              state=current_menu.name, service_code=service_code)

        session.user = user
        session.ussd_menu = current_menu

        db.session.add(session)

    return session
