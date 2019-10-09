from server.models.ussd import UssdMenu, UssdSession


class KenyaUssdProcessor:
    @staticmethod
    def process_request(session_id: str, msisdn: str, user_input: str) -> UssdMenu:
        #TODO(ussd)
        return UssdMenu.query.filter_by(name='exit_invalid_request').first()

    @staticmethod
    def replace_vars(current_menu: UssdMenu, ussd_session: UssdSession, display_text: str) -> str:
        return "TODO(ussd)"
