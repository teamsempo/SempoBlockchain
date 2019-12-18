from flask import Blueprint, request, make_response
from flask.views import MethodView

from server import db
from server.utils.auth import show_all, requires_auth
from server.models.user import User
from server.models.ussd import UssdMenu
from server.utils.phone import proccess_phone_number
from server.utils.ussd.kenya_ussd_processor import KenyaUssdProcessor
from server.utils.ussd.ussd import menu_display_text_in_lang, create_or_update_session

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
    @show_all
    @requires_auth(allowed_basic_auth_types=('external',), allow_query_string_auth=True)
    def post(self):
        post_data = request.get_json() or request.form

        session_id = post_data.get('sessionId')
        phone_number = post_data.get('phoneNumber')
        user_input = post_data.get('text')
        service_code = post_data.get('serviceCode')

        if phone_number:
            msisdn = proccess_phone_number(phone_number, 'KE')
            user = User.query.execution_options(show_all=True).filter_by(phone=msisdn).first()
            # api chains all inputs that came through with *
            latest_input = user_input.split('*')[-1]
            # TODO(ussd): 'exit_not_registered' if no user
            if None in [user, msisdn, session_id]:
                current_menu = UssdMenu.find_by_name('exit_invalid_request')
                text = menu_display_text_in_lang(current_menu, user)
            else:
                current_menu = KenyaUssdProcessor.process_request(session_id, latest_input, user)
                ussd_session = create_or_update_session(session_id, user, current_menu, user_input, service_code)
                text = KenyaUssdProcessor.custom_display_text(current_menu, ussd_session, user)
                if text is None:
                    text = menu_display_text_in_lang(current_menu, user)
                if "CON" not in text and "END" not in text:
                    raise Exception("no menu found. text={}, user={}, menu={}, session={}".format(text, user.id, current_menu.name, ussd_session.id))

                db.session.commit()
        else:
            current_menu = UssdMenu.find_by_name('exit_invalid_request')
            text = menu_display_text_in_lang(current_menu, None)

        return make_response(text), 200


ussd_blueprint.add_url_rule(
    '/ussd/kenya',
    view_func=ProcessKenyaUssd.as_view('ussd_kenya__view'),
    methods=['POST']
)
