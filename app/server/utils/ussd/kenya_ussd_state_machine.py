"""
This class contains the KenyaUssdStateMachine responsible for managing the states of the ussd application
as would apply to its use in kenya.
It manages transitions between different states of the ussd system based on user input.
The class contains methods responsible for validation of user input and processing user input to facilitate
the services provided by the  ussd app.
"""
from transitions import Machine
import re

from server import db
from server.models.user import User
from server.utils.phone import proccess_phone_number, send_generic_message
from server.models.ussd import UssdSession

"""
Guards for menu selection
"""


def user_object(user_phone):
    return User.query.filter_by(phone=proccess_phone_number(user_phone)).first()


# conditions and guards for menu selections
def menu_two_selected(user_input):
    selection = user_input == '2'
    return selection


def menu_three_selected(user_input):
    selection = user_input == '3'
    return selection


def menu_four_selected(user_input):
    selection = user_input == '4'
    return selection


def menu_five_selected(user_input):
    selection = user_input == '5'
    return selection


def menu_ten_selected(user_input):
    selection = user_input == '10'
    return selection


def is_valid_pin(user_pin):
    pin_validity = False
    if len(user_pin) == 4 and re.match(r"\d", user_pin):
        pin_validity = True
    return pin_validity


# TODO: [Philip] Find way to compare pin entered in previous transition to pin in initial_pin_confirmation transitions
def new_pins_match(user_confirmation_pin):
    pass


def recipient_exists(recipient_phone):
    recipient = user_object(recipient_phone)
    return recipient.count() == 1


# TODO: [Philip] Create provision to access USSD Session from class, may require it in constructor
def recipient_not_initiator(recipient_phone, session):
    return session.msisdn != proccess_phone_number(recipient_phone)


# TODO: [Philip] User model differs from GE User model confirm this active status is the same
def user_active(user_phone):
    user = user_object(user_phone)
    return user.is_activated


# TODO: [Philip] Find out how token agents and other user roles are stored
def user_not_token_agent(user_phone):
    user_object(user_phone)
    pass


def token_agent_exists(user_phone):
    user_object(user_phone)
    pass


class KenyaUssdStateMachine:
    # define machine states
    states = ['start',
              'initial_language_selection',
              'initial_pin_entry',
              'initial_pin_confirmation',
              # send token states
              'send_enter_recipient',
              'send_choose_token',
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
              'exchange_token_confirmation'
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

    # initialize machine
    def __init__(self, session: UssdSession):
        self.session = session
        self.machine = Machine(model=self,
                               states=self.states,
                               initial=session.state)

        # event: initial_language_selection transitions
        initial_language_selection_transitions = [
            {'trigger': 'feed_char',
             'source': 'initial_language_selection',
             'dest': 'complete',
             'after': 'change_preferred_language'},
            {'trigger': 'feed_char',
             'source': 'initial_language_selection',
             'dest': 'help',
             'conditions': 'menu_three_selected'},
            {'trigger': 'feed_char',
             'source': 'initial_language_selection',
             'dest': 'exit_invalid_menu_option'}
        ]
        self.machine.add_transitions(initial_language_selection_transitions)

        # event: initial_pin_entry transitions
        initial_pin_entry_transitions = [
            {'trigger': 'feed_char',
             'source': 'initial_pin_entry',
             'dest': 'initial_pin_confirmation',
             'conditions': 'is_valid_pin'},
            {'trigger': 'feed_char',
             'source': 'initial_pin_entry',
             'dest': 'exit_invalid_pin'}
        ]
        self.machine.add_transitions(initial_pin_entry_transitions)

        # event: initial_pin_confirmation transitions
        initial_pin_confirmation_transitions = [
            {'trigger': 'feed_char',
             'source': 'initial_pin_confirmation',
             'dest': 'complete',
             'conditions': 'new_pins_match'},
            {'trigger': 'feed_char',
             'source': 'initial_pin_confirmation',
             'dest': 'exit_pin_mismatch'}
        ]
        self.machine.add_transitions(initial_pin_confirmation_transitions)

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
        self.machine.add_transitions(start_transitions)

        # event: send_enter_recipient transitions
        send_enter_recipient_transitions = [
            {'trigger': 'feed_char',
             'source': 'send_enter_recipient',
             'dest': 'send_token_amount',
             'conditions': 'is_valid_recipient',
             'after': 'save_recipient_phone'},
            {'trigger': 'feed_char',
             'source': 'send_enter_recipient',
             'dest': 'exit_use_exchange_menu',
             'conditions': 'token_agent_exists',
             'after': 'save_recipient_phone'},
            {'trigger': 'feed_char',
             'source': 'send_enter_recipient',
             'dest': 'exit_invalid_recipient',
             'after': 'upsell_unregistered_recipient'}
        ]
        self.machine.add_transitions(send_enter_recipient_transitions)

        # event: send_choose_token transitions
        send_choose_token_transitions = [
            {'trigger': 'feed_char',
             'source': 'send_choose_token',
             'dest': 'send_token_amount',
             'after': 'save_community_token_id'}
        ]
        self.machine.add_transitions(send_choose_token_transitions)

        # event: send_token_amount transitions
        send_token_amount_transitions = [
            {'trigger': 'feed_char',
             'source': 'send_token_amount',
             'dest': 'send_token_reason',
             'after': 'save_transaction_amount'}
        ]
        self.machine.add_transitions(send_token_amount_transitions)

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
        self.machine.add_transitions(send_token_reason_transitions)

        # event: send_token_reason_other transitions
        send_token_reason_other_transitions = [
            {'trigger': 'feed_char',
             'source': 'send_token_reason_other',
             'dest': 'send_token_pin_authorization',
             'after': 'save_transaction_reason_other'}
        ]
        self.machine.add_transitions(send_token_reason_other_transitions)

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
        self.machine.add_transitions(send_token_pin_authorization_transitions)

        # event: send_token_confirmation transitions
        send_token_confirmation_transitions = [
            {'trigger': 'feed_char',
             'source': 'send_token_confirmation',
             'dest': 'complete',
             'conditions': 'menu_one_selected',
             'after': 'process_send_token_request'},
            {'trigger': 'feed_char',
             'source': 'send_token_confirmation',
             'dest': 'exit',
             'conditions': 'menu_two_selected'},
            {'trigger': 'feed_char',
             'source': 'send_token_confirmation',
             'dest': 'exit_invalid_menu_option'}
        ]
        self.machine.add_transitions(send_token_confirmation_transitions)

        # event: convert_token_from transitions
        convert_token_from_transitions = [
            {'trigger': 'feed_char',
             'source': 'convert_token_from',
             'dest': 'convert_token_amount',
             'after': 'save_convert_from_token_id'}
        ]
        self.machine.add_transitions(convert_token_from_transitions)

        # event: account_management transitions
        account_management_transitions = [
            {'trigger': 'feed_char',
             'source': 'account_management',
             'dest': 'my_business',
             'conditions': 'menu_one_selected',
             'after': 'process_send_token_request'},
            {'trigger': 'feed_char',
             'source': 'account_management',
             'dest': 'choose_language',
             'conditions': 'menu_two_selected'},
            {'trigger': 'feed_char',
             'source': 'account_management',
             'dest': 'balance_inquiry_pin_authorization',
             'conditions': 'menu_two_selected'},
            {'trigger': 'feed_char',
             'source': 'account_management',
             'dest': 'current_pin',
             'conditions': 'menu_three_selected'},
            {'trigger': 'feed_char',
             'source': 'account_management',
             'dest': 'opt_out_of_market_place_pin_authorization',
             'conditions': 'menu_four_selected'},
            {'trigger': 'feed_char',
             'source': 'account_management',
             'dest': 'exit_invalid_menu_option'}
        ]
        self.machine.add_transitions(account_management_transitions)

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
        self.machine.add_transitions(my_business_transitions)

        # event: choose_language transitions
        choose_language_transitions = [
            {'trigger': 'feed_char',
             'source': 'choose_language',
             'dest': 'complete',
             'after': 'change_preferred_language'}
        ]
        self.machine.add_transitions(choose_language_transitions)

        # event: balance_inquiry_pin_authorization transitions
        balance_inquiry_pin_authorization_transitions = [
            {'trigger': 'feed_char',
             'source': 'balance_inquiry_pin_authorization',
             'dest': 'complete',
             'conditions': 'is_authorized_pin'},
            {'trigger': 'feed_char',
             'source': 'balance_inquiry_pin_authorization',
             'dest': 'exit_pin_blocked',
             'conditions': 'is_blocked_pin'}
        ]
        self.machine.add_transitions(balance_inquiry_pin_authorization_transitions)

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
        self.machine.add_transitions(current_pin_transitions)

        # event: new_pin transitions
        new_pin_transitions = [
            {'trigger': 'feed_char',
             'source': 'new_pin',
             'dest': 'new_pin_confirmation',
             'conditions': 'is_valid_new_pin'},
            {'trigger': 'feed_char',
             'source': 'new_pin',
             'dest': 'exit_invalid_pin'}
        ]
        self.machine.add_transitions(new_pin_transitions)

        # event: new_pin_confirmation transitions
        new_pin_confirmation = [
            {'trigger': 'feed_char',
             'source': 'new_pin_confirmation',
             'dest': 'complete',
             'conditions': 'new_pins_match'},
            {'trigger': 'feed_char',
             'source': 'new_pin_confirmation',
             'dest': 'exit_pin_mismatch'}
        ]
        self.machine.add_transitions(new_pin_confirmation)

        # event: opt_out_of_market_place_pin_authorization transitions
        opt_out_of_market_place_pin_authorization_transitions = [
            {'trigger': 'feed_char',
             'source': 'opt_out_of_market_place_pin_authorization',
             'dest': 'complete',
             'conditions': 'is_authorized_pin',
             'after': 'change_opt_in_market_status'},
            {'trigger': 'feed_char',
             'source': 'opt_out_of_market_place_pin_authorization',
             'dest': 'exit_pin_blocked',
             'conditions': 'is_blocked_pin'}
        ]
        self.machine.add_transitions(opt_out_of_market_place_pin_authorization_transitions)

        # event: exchange_token transitions
        exchange_token_transitions = [
            {'trigger': 'feed_char',
             'source': 'exchange_token',
             'dest': 'exchange_rate_pin_authorization',
             'conditions': 'menu_one_selected',
             'after': 'process_send_token_request'},
            {'trigger': 'feed_char',
             'source': 'exchange_token',
             'dest': 'exchange_token_agent_number_entry',
             'conditions': 'menu_two_selected'},
            {'trigger': 'feed_char',
             'source': 'exchange_token',
             'dest': 'exit_invalid_menu_option'}
        ]
        self.machine.add_transitions(exchange_token_transitions)

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
        self.machine.add_transitions(exchange_rate_pin_authorization_transitions)

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
        self.machine.add_transitions(exchange_token_agent_number_entry_transitions)

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
        self.machine.add_transitions(exchange_token_amount_entry_transitions)

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
        self.machine.add_transitions(exchange_token_pin_authorization_transitions)

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
        self.machine.add_transitions(exchange_token_confirmation_transitions)

        # event: help transitions
        help_transitions = [
            {'trigger': 'feed_char',
             'source': 'help',
             'dest': 'complete'}
        ]
        self.machine.add_transitions(help_transitions)

    def menu_one_selected(self, user_input):
        return user_input == '1'

    def is_valid_recipient(self, char):
        recipient_validity = recipient_exists(char) \
                             and recipient_not_initiator(char,
                                                         self.session.id) \
                             and user_active(char)
        return recipient_validity

    def save_recipient_phone(self, char):
        session = self.session
        session.session_data = {'recipient_phone': char}
        db.session.commit()

    def upsell_unregistered_recipient(self, char):
        if recipient_exists(char):
            sender = user_object(self.session.msisdn)
            upsell_msg = f"{sender.full_name} amejaribu kukutumia #{sender.community_token.name} lakini hujasajili. " \
                         "Tuma information yako: jina, nambari ya simu, kitambulisho, eneo, na aina ya biashara yako " \
                         "kwa 0757628885 "
            send_generic_message(proccess_phone_number(char), upsell_msg)
