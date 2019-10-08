from server.models.ussd import UssdMenu


class KenyaUssdProcessor:
    @staticmethod
    def process_request(session_id, msisdn, user_input):
        #TODO(ussd)
        return UssdMenu.query.filter_by(name='exit_invalid_request').first()

    @staticmethod
    def replace_vars(current_menu, ussd_session, display_text):
        return "TODO(ussd)"
