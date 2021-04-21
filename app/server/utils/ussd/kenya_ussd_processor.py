from typing import Optional
import math

from server.models.ussd import UssdMenu, UssdSession
from server.models.user import User
from server.utils.user import get_user_by_phone, default_token
from server.utils.ussd.kenya_ussd_state_machine import KenyaUssdStateMachine, ITEMS_PER_MENU, USSD_MAX_LENGTH
from server.utils.internationalization import i18n_for
from server.utils.credit_transfer import cents_to_dollars


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
    def fit_usages(ussd_session, most_relevant_usages, blank_len, user, list_start, previous_stack):

        current_usages = []
        previous_set_of_options = ''
        last_index = 0
        for index, usage in enumerate(most_relevant_usages[list_start:]):
            current_usages.append(usage)
            menu_options = KenyaUssdProcessor.create_usages_list(current_usages, user)

            if len(menu_options) + blank_len > USSD_MAX_LENGTH or index + 1 > ITEMS_PER_MENU:
                continue

            previous_set_of_options = menu_options
            last_index = index

        ussd_session.set_data('usage_index_stack', previous_stack + [list_start + last_index + 1])

        return previous_set_of_options

    @staticmethod
    def custom_display_text(menu: UssdMenu, ussd_session: UssdSession) -> str:
        """
        Many USSD responses include user-specific data that is stored inside the USSD session. This function
        extracts the appropriate session data based on the current menu name and then inserts them as keywords in the
        i18n function.
        :param menu: The USSD menu to create a text response for
        :param ussd_session: The ussd session containing user data
        :return: raw ussd menu text string
        """

        user = ussd_session.user

        if menu.name == 'about_my_business':
            bio = next(filter(lambda x: x.name == 'bio', user.custom_attributes), None)
            if bio:
                bio_text = bio.value.strip('"')
            else:
                bio_text = None

            if bio_text is None or '':
                return i18n_for(user, "{}.none".format(menu.display_key))
            else:
                return i18n_for(user, "{}.bio".format(menu.display_key), user_bio=bio_text)

        if menu.name == 'send_token_confirmation':
            recipient = get_user_by_phone(ussd_session.get_data('recipient_phone'), 'KE', True)
            recipient_phone = recipient.user_details()
            token = default_token(user)
            transaction_amount = ussd_session.get_data('transaction_amount')
            transaction_reason = ussd_session.get_data('transaction_reason_i18n')
            return i18n_for(
                user, menu.display_key,
                recipient_phone=recipient_phone,
                token_name=token.symbol,
                transaction_amount=cents_to_dollars(transaction_amount),
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
                token_name=token.symbol,
                exchange_amount=cents_to_dollars(exchange_amount)
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

        if menu.name == 'directory_listing' or menu.name == 'send_token_reason':

            blank_template = i18n_for(
                user, menu.display_key, options=''
            )

            blank_len = len(blank_template)

            most_relevant_usages = ussd_session.get_data('transfer_usage_mapping')

            options = KenyaUssdProcessor.fit_usages(
                ussd_session,
                most_relevant_usages,
                blank_len,
                user,
                0,
                [0]
            )

            # current_usages = most_relevant_usages[:ITEMS_PER_MENU]
            return i18n_for(
                user, menu.display_key,
                options=options
            )

        if menu.name == 'directory_listing_other' or menu.name == 'send_token_reason_other':

            most_relevant_usages = ussd_session.get_data('transfer_usage_mapping')
            usage_menu_nr = ussd_session.get_data('usage_menu')
            usage_stack = ussd_session.get_data('usage_index_stack') or [0]

            start_of_list = usage_stack[usage_menu_nr]

            total_usages = len(most_relevant_usages)

            # First see if we can fit remaining usages onto the one page
            if start_of_list + ITEMS_PER_MENU > total_usages:
                part = 'first' if start_of_list == 0 else 'last'
                current_usages = most_relevant_usages[start_of_list:total_usages]
                menu_options = KenyaUssdProcessor.create_usages_list(current_usages, user)

                translated_menu = i18n_for(
                    user, "{}.{}".format(menu.display_key, part),
                    other_options=menu_options
                )

                if len(translated_menu) <= USSD_MAX_LENGTH:
                    return translated_menu

            # Oh well, guess we just have to fit as many as possible then

            part = 'first' if start_of_list == 0 else 'middle'

            blank_template = i18n_for(
                user, "{}.{}".format(menu.display_key, part),
                other_options=''
            )

            blank_len = len(blank_template)

            options = KenyaUssdProcessor.fit_usages(
                ussd_session,
                most_relevant_usages,
                blank_len,
                user,
                start_of_list,
                usage_stack)

            # current_usages = most_relevant_usages[:ITEMS_PER_MENU]
            return i18n_for(
                user, "{}.{}".format(menu.display_key, part),
                other_options=options
            )

        return i18n_for(user, menu.display_key)

    @staticmethod
    def create_usages_list(usages, user):
        menu_options = ''
        for i, usage in enumerate(usages):
            business_usage_string = None
            if usage.get('translations') is not None and user.preferred_language is not None:
                business_usage_string = usage.get('translations').get(
                    user.preferred_language)
            if business_usage_string is None:
                business_usage_string = usage.get('name')
            message_option = '%d. %s' % (i+1, business_usage_string)
            if i < len(usages):
                message_option += '\n'
            menu_options += message_option
        return menu_options[:-1]
