from typing import Optional

from server import db
from server.models.ussd import UssdMenu, UssdSession
from server.models.user import User
from server.utils.user import get_user_by_phone, default_token
from server.utils.ussd.kenya_ussd_state_machine import KenyaUssdStateMachine
from server.utils.i18n import i18n_for


class KenyaUssdProcessor:
    @staticmethod
    def process_request(session_id: str, user_input: str, user: User) -> UssdMenu:
        session: Optional[UssdSession] = UssdSession.query.filter_by(session_id=session_id).first()
        # returning session
        if session:
            if user_input == "":
                return UssdMenu.find_by_name('exit_invalid_input')
            elif user_input == '0':
                return UssdMenu.find_by_name(session.state).parent()
            else:
                new_state = KenyaUssdProcessor.next_state(session, user_input, user)
                return UssdMenu.find_by_name(new_state)
        # new session
        else:
            if user.has_valid_pin():
                return UssdMenu.find_by_name('start')
            else:
                if user.failed_pin_attempts is not None and user.failed_pin_attempts >= 3:
                    return UssdMenu.find_by_name('exit_pin_blocked')
                elif user.preferred_language is None:
                    return UssdMenu.find_by_name('initial_language_selection')
                else:
                    return UssdMenu.find_by_name('initial_pin_entry')

    @staticmethod
    def next_state(session: UssdSession, user_input: str, user: User) -> UssdMenu:
        state_machine = KenyaUssdStateMachine(session, user)
        state_machine.feed_char(user_input)
        new_state = state_machine.state

        session.state = new_state
        return new_state

    @staticmethod
    def custom_display_text(menu: UssdMenu, ussd_session: UssdSession, user: User) -> Optional[str]:
        if menu.name == 'about_my_business':
            bio = user.custom_attributes.filter_by(name='bio').first()
            if bio is None:
                return i18n_for(user, 'about_my_business_none')
            else:
                return i18n_for(user, menu.display_key, user_bio=bio)

        if menu.name == 'send_token_confirmation':
            recipient = get_user_by_phone(ussd_session.get_data('recipient_phone'), 'KE', True)
            recipient_phone = recipient.user_details()
            token = default_token(user)
            transaction_amount = ussd_session.get_data('transaction_amount')
            transaction_reason = ussd_session.get_data('transaction_reason_translated')
            return i18n_for(
                user, menu.display_key,
                recipient_phone=recipient_phone,
                token_name=token.name,
                transaction_amount=transaction_amount,
                transaction_reason=transaction_reason
            )

        if menu.name == 'exchange_token_confirmation':
            agent = get_user_by_phone(ussd_session.get_data('agent_phone'), 'KE', True)
            agent_phone = agent.user_details()
            token = default_token(user)
            exchange_amount = ussd_session.get_data('exchange_amount')
            return i18n_for(
                user, menu.display_key,
                agent_phone=agent_phone,
                token_name=token.name,
                exchange_amount=exchange_amount
            )

        # in matching is scary since it might pick up unintentional ones
        if 'exit' in menu.name or 'help' == menu.name:
            return i18n_for(
                user, menu.display_key,
                support_phone='+254757628885'
            )

        # in matching is scary since it might pick up unintentional ones
        if 'pin_authorization' in menu.name or 'current_pin' == menu.name:
            if user.failed_pin_attempts is not None and user.failed_pin_attempts > 0:
                return i18n_for(
                    user, "{}.retry".format(menu.display_key),
                    remaining_attempts=3 - user.failed_pin_attempts
                )
            else:
                return i18n_for(user, "{}.first".format(menu.display_key))

        return None




