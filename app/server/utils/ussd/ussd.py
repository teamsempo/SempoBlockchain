from typing import Optional

from server import db
from server.models.user import User
from server.models.ussd import UssdMenu, UssdSession


# TODO: in the future this should handle i18n more generally
def menu_display_text_in_lang(current_menu: UssdMenu, user: Optional[User]) -> str:
    if user is None or user.preferred_language is None:
        return current_menu.display_text_en
    else:
        if user.preferred_language == "sw_KE":
            return current_menu.display_text_sw
        else:
            return current_menu.display_text_en


def create_or_update_session(session_id: str, user: User, current_menu: UssdMenu, user_input: str, service_code: str) -> UssdSession:
    session = UssdSession.query.filter_by(session_id=session_id)
    if session.count() > 0:
        session.update({"user_input": user_input, "ussd_menu_id": current_menu.id, "state": current_menu.name})
        db.session.commit()
    else:
        session = UssdSession(session_id=session_id, user_id=user.id, msisdn=user.phone, user_input=user_input,
                              ussd_menu_id=current_menu.id, state=current_menu.name, service_code=service_code)
        db.session.add(session)
        db.session.commit()

    return session
