from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView

from server.models.user import User
from server.models.ussd import UssdMenu
from server.utils.phone import proccess_phone_number

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
                current_menu = UssdMenu.query
                """
                    TODO(ussd)
                    current_menu = UssdMenu.find_by(name: 'exit_invalid_request')
                    menu_display_text = menu_display_text_in_lang(current_menu, user.preferred_language)
                    render plain: menu_display_text
                """
                text = "exit_invalid_request"
            else:
                """
                    TODO(ussd)
                    current_menu = UssdApi::MenuProcessor.process_request(ussd_request.attributes)
                    ussd_session = create_or_update_session(ussd_request.attributes, current_menu)
                    menu_display_text = menu_display_text_in_lang(current_menu, user &.preferred_language)
                    render plain: UssdApi::MenuProcessor.replace_vars(current_menu, ussd_session, menu_display_text)
                """
                text = "test"
        else:
            #TODO(ussd): render plain: UssdMenu.find_by(name: 'exit_invalid_request').display_text
            text = "test2"

        return make_response(text, 200)


ussd_blueprint.add_url_rule(
    '/v1/ussd/kenya',
    view_func=ProcessKenyaUssd.as_view('ussd_kenya__view'),
    methods=['POST']
)
