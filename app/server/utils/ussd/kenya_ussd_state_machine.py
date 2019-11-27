"""
This file (kenya_ussd_state_machine.py) contains the KenyaUssdStateMachine responsible for managing the states of
the ussd application as would apply to its use in kenya.
It manages transitions between different states of the ussd system based on user input.
The class contains methods responsible for validation of user input and processing user input to facilitate
the services provided by the  ussd app.
"""
import re

from transitions import Machine

from server import message_processor, sentry, ussd_tasker
from server.models.organisation import Organisation
from server.models.user import User
from server.models.ussd import UssdSession
from server.models.transfer_usage import TransferUsage
from server.utils.i18n import i18n_for
from server.utils.user import set_custom_attributes, change_initial_pin, change_current_pin, default_token, get_user_by_phone


class KenyaUssdStateMachine(Machine):
    # define machine states
    states = [
        'feed_char',
        'start',
        'initial_language_selection',
        'initial_pin_entry',
        'initial_pin_confirmation',
        # send token states
        'send_enter_recipient',
        'send_token_amount',
        'send_token_reason',
        'send_token_reason_other',
        'send_token_pin_authorization',
        'send_token_confirmation',
        # account management states
        'account_management',
        'balance_inquiry_pin_authorization',
        'choose_language',
        'pin_change',
        'current_pin',
        'new_pin',
        'new_pin_confirmation',
        'my_business',
        'about_my_business',
        'change_my_business_prompt',
        'opt_out_of_market_place_pin_authorization',
        # directory listing state
        'directory_listing',
        # exchange token states
        'exchange_token',
        'exchange_rate_pin_authorization',
        'exchange_token_agent_number_entry',
        'exchange_token_amount_entry',
        'exchange_token_pin_authorization',
        'exchange_token_confirmation',
        # help state
        'help',
        # exit states
        'exit',
        'exit_not_registered',
        'exit_invalid_menu_option',
        'exit_invalid_recipient',
        'exit_use_exchange_menu',
        'exit_wrong_pin',
        'exit_invalid_pin',
        'exit_pin_mismatch',
        'exit_pin_blocked',
        'exit_invalid_token_agent',
        'exit_invalid_exchange_amount',
        'complete'
    ]

    def send_sms(self, phone, message_key, **kwargs):
        message = i18n_for(self.user, "ussd.kenya.{}".format(message_key), **kwargs)
        message_processor.send_message(phone, message)

    def change_preferred_language_to_sw(self, user_input):
        self.change_preferred_language_to("sw")

    def change_preferred_language_to_en(self, user_input):
        self.change_preferred_language_to("en")

    def change_preferred_language_to(self, language):
        self.user.preferred_language = language
        self.send_sms(self.user.phone, "language_change_sms")

    def save_business_directory_info(self, user_input):
        attrs = {
            "custom_attributes": {
                "bio": user_input
            }
        }
        set_custom_attributes(attrs, self.user)

    def change_opted_in_market_status(self, user_input):
        attrs = {
            "custom_attributes": {
                "market_enabled": False
            }
        }
        set_custom_attributes(attrs, self.user)
        self.send_sms(self.user.phone, "opt_out_of_market_place_sms")

    def save_pin_data(self, user_input):
        self.session.set_data('initial_pin', user_input)

    def is_valid_pin(self, user_input):
        pin_validity = False
        if len(user_input) == 4 and re.match(r"\d", user_input):
            pin_validity = True
        return pin_validity

    def new_pins_match(self, user_input):
        pins_match = False
        # get previous pin input
        initial_pin = self.session.get_data('initial_pin')
        if user_input == initial_pin:
            pins_match = True
        return pins_match

    def authorize_pin(self, pin):
        authorized = False
        if self.user.failed_pin_attempts is None:
            self.user.failed_pin_attempts = 0
        if self.user.failed_pin_attempts >= 3:
            return False
        if self.user.failed_pin_attempts < 3:
            authorized = self.user.verify_pin(pin)
            if authorized:
                if self.user.failed_pin_attempts > 0:
                    self.user.failed_pin_attempts = 0
            else:
                self.user.failed_pin_attempts += 1
        return authorized

    def complete_initial_pin_change(self, user_input):
        change_initial_pin(user=self.user, new_pin=user_input)

    def complete_pin_change(self, user_input):
        change_current_pin(user=self.user, new_pin=user_input)

    def is_authorized_pin(self, user_input):
        return self.authorize_pin(user_input)

    def is_blocked_pin(self, user_input):
        return self.user.failed_pin_attempts is not None and self.user.failed_pin_attempts == 3

    def is_valid_new_pin(self, user_input):
        return self.is_valid_pin(user_input) and not self.user.verify_pin(user_input)

    # recipient exists, is not initiator, matches active and agent requirements
    def is_valid_recipient(self, user, should_be_active, should_be_agent):
        return user is not None and \
            user.phone != self.user.phone and \
            user.is_disabled != should_be_active and \
            user.has_token_agent_role == should_be_agent

    def is_user(self, user_input):
        user = get_user_by_phone(user_input, "KE")
        return self.is_valid_recipient(user, True, False)

    def is_token_agent(self, user_input):
        user = get_user_by_phone(user_input, "KE")
        return self.is_valid_recipient(user, True, True)

    def save_recipient_phone(self, user_input):
        self.session.set_data('recipient_phone', user_input)

    def save_transaction_amount(self, user_input):
        self.session.set_data('transaction_amount', user_input)

    def save_transaction_reason(self, user_input):
        #TODO: use ruben's dynamic code to convert number to reason
        self.session.set_data('transaction_reason_translated', user_input)
        self.session.set_data('transaction_reason_id', "1")

    def save_transaction_reason_other(self, user_input):
        self.session.set_data('transaction_reason_translated', user_input)
        self.session.set_data('transaction_reason_id', "1")

    def process_send_token_request(self, user_input):
        user = get_user_by_phone(self.session.get_data('recipient_phone'), "KE")
        amount = float(self.session.get_data('transaction_amount'))
        reason_str = self.session.get_data('transaction_reason_translated')
        reason_id = float(self.session.get_data('transaction_reason_id'))
        ussd_tasker.send_token(self.user, user, amount, reason_str, reason_id)

    def upsell_unregistered_recipient(self, user_input):
        user = get_user_by_phone(user_input, "KE")
        if self.is_valid_recipient(user, False, False):
            self.send_sms(
                user.phone,
                'upsell_message',
                first_name=user.first_name,
                last_name=user.last_name,
                community_token=default_token(user).name
            )

    def inquire_balance(self, user_input):
        ussd_tasker.inquire_balance(self.user)

    def send_directory_listing(self, user_input):
        #TODO: replace with ruben's method when merge
        chosen_transfer_usage = TransferUsage.find_or_create("Food")

        try:
            ussd_tasker.send_directory_listing(self.user, chosen_transfer_usage)
        except Exception as e:
            print(e)
            sentry.captureException()
            pass

    def fetch_user_exchange_rate(self, user_input):
        ussd_tasker.fetch_user_exchange_rate(self.user)

    def is_valid_token_agent(self, user_input):
        user = get_user_by_phone(user_input, "KE", True)
        return user.has_token_agent_role

    def save_exchange_agent_phone(self, user_input):
        self.session.set_data('agent_phone', user_input)

    def is_valid_token_exchange_amount(self, user_input):
        return int(user_input) >= 40

    def save_exchange_amount(self, user_input):
        self.session.set_data('exchange_amount', user_input)

    def process_exchange_token_request(self, user_input):
        agent = get_user_by_phone(self.session.get_data('agent_phone'), "KE")
        amount = float(self.session.get_data('exchange_amount'))
        ussd_tasker.exchange_token(self.user, agent, amount)

    def menu_one_selected(self, user_input):
        return user_input == '1'

    def menu_two_selected(self, user_input):
        return user_input == '2'

    def menu_three_selected(self, user_input):
        return user_input == '3'

    def menu_four_selected(self, user_input):
        return user_input == '4'

    def menu_five_selected(self, user_input):
        return user_input == '5'

    def menu_ten_selected(self, user_input):
        return user_input == '10'

    # initialize machine
    def __init__(self, session: UssdSession, user: User):
        self.session = session
        self.user = user
        Machine.__init__(
            self,
            model=self,
            states=self.states,
            initial=session.state
        )

        # event: initial_language_selection transitions
        initial_language_selection_transitions = [
            {'trigger': 'feed_char',
             'source': 'initial_language_selection',
             'dest': 'complete',
             'after': 'change_preferred_language_to_en',
             'conditions': 'menu_one_selected'},
            {'trigger': 'feed_char',
             'source': 'initial_language_selection',
             'dest': 'complete',
             'after': 'change_preferred_language_to_sw',
             'conditions': 'menu_two_selected'},
            {'trigger': 'feed_char',
             'source': 'initial_language_selection',
             'dest': 'help',
             'conditions': 'menu_three_selected'},
            {'trigger': 'feed_char',
             'source': 'initial_language_selection',
             'dest': 'exit_invalid_menu_option'}
        ]
        self.add_transitions(initial_language_selection_transitions)

        # event: initial_pin_entry transitions
        initial_pin_entry_transitions = [
            {'trigger': 'feed_char',
             'source': 'initial_pin_entry',
             'dest': 'initial_pin_confirmation',
             'after': 'save_pin_data',
             'conditions': 'is_valid_pin'},
            {'trigger': 'feed_char',
             'source': 'initial_pin_entry',
             'dest': 'exit_invalid_pin'}
        ]
        self.add_transitions(initial_pin_entry_transitions)

        # event: initial_pin_confirmation transitions
        initial_pin_confirmation_transitions = [
            {'trigger': 'feed_char',
             'source': 'initial_pin_confirmation',
             'dest': 'complete',
             'after': 'complete_initial_pin_change',
             'conditions': 'new_pins_match'},
            {'trigger': 'feed_char',
             'source': 'initial_pin_confirmation',
             'dest': 'exit_pin_mismatch'}
        ]
        self.add_transitions(initial_pin_confirmation_transitions)

        # event: start transitions
        start_transitions = [
            {'trigger': 'feed_char',
             'source': 'start',
             'dest': 'send_enter_recipient',
             'conditions': 'menu_one_selected'},
            {'trigger': 'feed_char',
             'source': 'start',
             'dest': 'account_management',
             'conditions': 'menu_two_selected'},
            {'trigger': 'feed_char',
             'source': 'start',
             'dest': 'directory_listing',
             'conditions': 'menu_three_selected'},
            {'trigger': 'feed_char',
             'source': 'start',
             'dest': 'exchange_token',
             'conditions': 'menu_four_selected'},
            {'trigger': 'feed_char',
             'source': 'start',
             'dest': 'help',
             'conditions': 'menu_five_selected'},
            {'trigger': 'feed_char',
             'source': 'start',
             'dest': 'exit_invalid_menu_option'}
        ]
        self.add_transitions(start_transitions)

        # event: send_enter_recipient transitions
        send_enter_recipient_transitions = [
            {'trigger': 'feed_char',
             'source': 'send_enter_recipient',
             'dest': 'send_token_amount',
             'conditions': 'is_user',
             'after': 'save_recipient_phone'},
            {'trigger': 'feed_char',
             'source': 'send_enter_recipient',
             'dest': 'exit_use_exchange_menu',
             'conditions': 'is_token_agent'},
            {'trigger': 'feed_char',
             'source': 'send_enter_recipient',
             'dest': 'exit_invalid_recipient',
             'after': 'upsell_unregistered_recipient'}
        ]
        self.add_transitions(send_enter_recipient_transitions)

        # event: send_token_amount transitions
        self.add_transition(trigger='feed_char',
                            source='send_token_amount',
                            dest='send_token_reason',
                            after='save_transaction_amount')

        # event: send_token_reason transitions
        send_token_reason_transitions = [
            {'trigger': 'feed_char',
             'source': 'send_token_reason',
             'dest': 'send_token_reason_other',
             'conditions': 'menu_ten_selected'},
            {'trigger': 'feed_char',
             'source': 'send_token_reason',
             'dest': 'send_token_pin_authorization',
             'after': 'save_transaction_reason'}
        ]
        self.add_transitions(send_token_reason_transitions)

        # event: send_token_reason_other transition
        self.add_transition(trigger='feed_char',
                            source='send_token_reason_other',
                            dest='send_token_pin_authorization',
                            after='save_transaction_reason_other')

        # event: send_token_pin_authorization transitions
        send_token_pin_authorization_transitions = [
            {'trigger': 'feed_char',
             'source': 'send_token_pin_authorization',
             'dest': 'send_token_confirmation',
             'conditions': 'is_authorized_pin'},
            {'trigger': 'feed_char',
             'source': 'send_token_pin_authorization',
             'dest': 'exit_pin_blocked',
             'conditions': 'is_blocked_pin'}
        ]
        self.add_transitions(send_token_pin_authorization_transitions)

        # event: send_token_confirmation transitions
        send_token_confirmation_transitions = [
            {'trigger': 'feed_char',
             'source': 'send_token_confirmation',
             'dest': 'complete',
             'after': 'process_send_token_request',
             'conditions': 'menu_one_selected'},
            {'trigger': 'feed_char',
             'source': 'send_token_confirmation',
             'dest': 'exit',
             'conditions': 'menu_two_selected'},
            {'trigger': 'feed_char',
             'source': 'send_token_confirmation',
             'dest': 'exit_invalid_menu_option'}
        ]
        self.add_transitions(send_token_confirmation_transitions)

        # event: account_management transitions
        account_management_transitions = [
            {'trigger': 'feed_char',
             'source': 'account_management',
             'dest': 'my_business',
             'conditions': 'menu_one_selected'},
            {'trigger': 'feed_char',
             'source': 'account_management',
             'dest': 'choose_language',
             'conditions': 'menu_two_selected'},
            {'trigger': 'feed_char',
             'source': 'account_management',
             'dest': 'balance_inquiry_pin_authorization',
             'conditions': 'menu_three_selected'},
            {'trigger': 'feed_char',
             'source': 'account_management',
             'dest': 'current_pin',
             'conditions': 'menu_four_selected'},
            {'trigger': 'feed_char',
             'source': 'account_management',
             'dest': 'opt_out_of_market_place_pin_authorization',
             'conditions': 'menu_five_selected'},
            {'trigger': 'feed_char',
             'source': 'account_management',
             'dest': 'exit_invalid_menu_option'}
        ]
        self.add_transitions(account_management_transitions)

        # event: my_business transitions
        my_business_transitions = [
            {'trigger': 'feed_char',
             'source': 'my_business',
             'dest': 'about_my_business',
             'conditions': 'menu_one_selected'},
            {'trigger': 'feed_char',
             'source': 'my_business',
             'dest': 'change_my_business_prompt',
             'conditions': 'menu_two_selected'}
        ]
        self.add_transitions(my_business_transitions)

        # event change_my_business_prompt transition
        self.add_transition(trigger='feed_char',
                            source='change_my_business_prompt',
                            dest='exit',
                            after='save_business_directory_info')

        # event: choose_language transition
        choose_language_transitions = [
            {'trigger': 'feed_char',
             'source': 'choose_language',
             'dest': 'complete',
             'after': 'change_preferred_language_to_en',
             'conditions': 'menu_one_selected'},
            {'trigger': 'feed_char',
             'source': 'choose_language',
             'dest': 'complete',
             'after': 'change_preferred_language_to_sw',
             'conditions': 'menu_two_selected'},
            {'trigger': 'feed_char',
             'source': 'choose_language',
             'dest': 'exit_invalid_menu_option'}
        ]
        self.add_transitions(choose_language_transitions)

        # event: balance_inquiry_pin_authorization transitions
        balance_inquiry_pin_authorization_transitions = [
            {'trigger': 'feed_char',
             'source': 'balance_inquiry_pin_authorization',
             'dest': 'complete',
             'conditions': 'is_authorized_pin',
             'after': 'inquire_balance'
             },
            {'trigger': 'feed_char',
             'source': 'balance_inquiry_pin_authorization',
             'dest': 'exit_pin_blocked',
             'conditions': 'is_blocked_pin'}
        ]
        self.add_transitions(balance_inquiry_pin_authorization_transitions)

        # event: current_pin transitions
        current_pin_transitions = [
            {'trigger': 'feed_char',
             'source': 'current_pin',
             'dest': 'new_pin',
             'conditions': 'is_authorized_pin'},
            {'trigger': 'feed_char',
             'source': 'current_pin',
             'dest': 'exit_pin_blocked',
             'conditions': 'is_blocked_pin'}
        ]
        self.add_transitions(current_pin_transitions)

        # event: new_pin transitions
        new_pin_transitions = [
            {'trigger': 'feed_char',
             'source': 'new_pin',
             'dest': 'new_pin_confirmation',
             'after': 'save_pin_data',
             'conditions': 'is_valid_new_pin'},
            {'trigger': 'feed_char',
             'source': 'new_pin',
             'dest': 'exit_invalid_pin'}
        ]
        self.add_transitions(new_pin_transitions)

        # event: new_pin_confirmation transitions
        new_pin_confirmation = [
            {'trigger': 'feed_char',
             'source': 'new_pin_confirmation',
             'dest': 'complete',
             'conditions': 'new_pins_match',
             'after': 'complete_pin_change'},
            {'trigger': 'feed_char',
             'source': 'new_pin_confirmation',
             'dest': 'exit_pin_mismatch'}
        ]
        self.add_transitions(new_pin_confirmation)

        # event: opt_out_of_market_place_pin_authorization transitions
        opt_out_of_market_place_pin_authorization_transitions = [
            {'trigger': 'feed_char',
             'source': 'opt_out_of_market_place_pin_authorization',
             'dest': 'complete',
             'conditions': 'is_authorized_pin',
             'after': 'change_opted_in_market_status'},
            {'trigger': 'feed_char',
             'source': 'opt_out_of_market_place_pin_authorization',
             'dest': 'exit_pin_blocked',
             'conditions': 'is_blocked_pin'}
        ]
        self.add_transitions(opt_out_of_market_place_pin_authorization_transitions)

        # event: directory_listing transitions
        self.add_transition(trigger='feed_char',
                            source='directory_listing',
                            dest='complete',
                            after='send_directory_listing')

        # event: exchange_token transitions
        exchange_token_transitions = [
            {'trigger': 'feed_char',
             'source': 'exchange_token',
             'dest': 'exchange_rate_pin_authorization',
             'conditions': 'menu_one_selected',
             'after': 'fetch_user_exchange_rate'},
            {'trigger': 'feed_char',
             'source': 'exchange_token',
             'dest': 'exchange_token_agent_number_entry',
             'conditions': 'menu_two_selected'},
            {'trigger': 'feed_char',
             'source': 'exchange_token',
             'dest': 'exit_invalid_menu_option'}
        ]
        self.add_transitions(exchange_token_transitions)

        # event: exchange_rate_pin_authorization transitions
        exchange_rate_pin_authorization_transitions = [
            {'trigger': 'feed_char',
             'source': 'exchange_rate_pin_authorization',
             'dest': 'complete',
             'conditions': 'is_authorized_pin',
             'after': 'fetch_user_exchange_rate'},
            {'trigger': 'feed_char',
             'source': 'exchange_rate_pin_authorization',
             'dest': 'exit_pin_blocked',
             'conditions': 'is_blocked_pin'}
        ]
        self.add_transitions(exchange_rate_pin_authorization_transitions)

        # event: exchange_token_agent_number_entry transitions
        exchange_token_agent_number_entry_transitions = [
            {'trigger': 'feed_char',
             'source': 'exchange_token_agent_number_entry',
             'dest': 'exchange_token_amount_entry',
             'conditions': 'is_valid_token_agent',
             'after': 'save_exchange_agent_phone'},
            {'trigger': 'feed_char',
             'source': 'exchange_token_agent_number_entry',
             'dest': 'exit_invalid_token_agent'}
        ]
        self.add_transitions(exchange_token_agent_number_entry_transitions)

        # event: exchange_token_amount_entry transitions
        exchange_token_amount_entry_transitions = [
            {'trigger': 'feed_char',
             'source': 'exchange_token_amount_entry',
             'dest': 'exchange_token_pin_authorization',
             'conditions': 'is_valid_token_exchange_amount',
             'after': 'save_exchange_amount'},
            {'trigger': 'feed_char',
             'source': 'exchange_token_amount_entry',
             'dest': 'exit_invalid_exchange_amount'}
        ]
        self.add_transitions(exchange_token_amount_entry_transitions)

        # event: exchange_token_pin_authorization transitions
        exchange_token_pin_authorization_transitions = [
            {'trigger': 'feed_char',
             'source': 'exchange_token_pin_authorization',
             'dest': 'exchange_token_confirmation',
             'conditions': 'is_authorized_pin'},
            {'trigger': 'feed_char',
             'source': 'exchange_token_pin_authorization',
             'dest': 'exit_pin_blocked',
             'conditions': 'is_blocked_pin'}
        ]
        self.add_transitions(exchange_token_pin_authorization_transitions)

        # event: exchange_token_confirmation transitions
        exchange_token_confirmation_transitions = [
            {'trigger': 'feed_char',
             'source': 'exchange_token_confirmation',
             'dest': 'complete',
             'conditions': 'menu_one_selected',
             'after': 'process_exchange_token_request'},
            {'trigger': 'feed_char',
             'source': 'exchange_token_confirmation',
             'dest': 'exit',
             'conditions': 'menu_two_selected'},
            {'trigger': 'feed_char',
             'source': 'exchange_token_confirmation',
             'dest': 'exit_invalid_menu_option'}
        ]
        self.add_transitions(exchange_token_confirmation_transitions)
