from flask import Blueprint, request, make_response
from flask.views import MethodView

from server import db
from server.models.user import User
from server.models.ussd import UssdMenu, UssdSession
from server.utils.phone import proccess_phone_number
from server.utils.ussd.kenya_ussd import KenyaUssdProcessor

ussd_blueprint = Blueprint('ussd', __name__)


class ProcessKenyaUssd(MethodView):
    """
        USSD Entry method
        Method: POST

        @params sessionId - USSD session ID
        @params phoneNumber - MSISDN initiating the USSD request
        @params serviceCode - USSD code dialled to access the service eg. *701#
        @params text - User input. The initial input is blank

        Method returns a text response to be displayed to the user's screen
        All responses mid-session begin with CON. All responses that terminate the session begin with the word END
    """

    def post(self):
        post_data = request.get_json()

        session_id = post_data.get('sessionId')
        phone_number = post_data.get('phoneNumber')
        user_input = post_data.get('text')

        if phone_number:
            msisdn = proccess_phone_number(phone_number, 'KE')
            user = User.query.filter_by(phone=msisdn).first()
            if None in [user, msisdn, session_id]:
                current_menu = UssdMenu.query.filter_by(name='exit_invalid_request').first()
                text = menu_display_text_in_lang(current_menu, user)
            else:
                current_menu = KenyaUssdProcessor.process_request(session_id, msisdn, user_input)
                ussd_session = create_or_update_session(session_id, user, current_menu, user_input)
                text = menu_display_text_in_lang(current_menu, user)
                text = KenyaUssdProcessor.replace_vars(current_menu, ussd_session, text)
        else:
            current_menu = UssdMenu.query.filter_by(name='exit_invalid_request').first()
            text = menu_display_text_in_lang(current_menu, None)

        return make_response(text, 200)


def menu_display_text_in_lang(current_menu: UssdMenu, user: User):
    if user is None or user.preferred_language is None:
        return current_menu.display_text_en
    else:
        if user.preferred_language == "sw_KE":
            return current_menu.display_text_sw
        else:
            return current_menu.display_text_en


def create_or_update_session(session_id, user: User, current_menu: UssdMenu, user_input):
    session = UssdSession.query.filter_by(session_id=session_id)
    if session is None:
        session = UssdSession(user_id=user.id, msisdn=user.phone, user_input=user_input,
                              ussd_menu_id=current_menu.id, state=current_menu.name)
        db.session.add(session)
    else:
        session.user_input = user_input
        session.ussd_menu_id = current_menu.id
        session.state = current_menu.name

    db.session.commit()
    return session


ussd_blueprint.add_url_rule(
    '/v1/ussd/kenya',
    view_func=ProcessKenyaUssd.as_view('ussd_kenya__view'),
    methods=['POST']
)
