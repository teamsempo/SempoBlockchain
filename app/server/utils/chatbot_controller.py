import datetime, re
from flask import current_app
from server import db
from server.models.chatbot_state import ChatbotState
from server.models.user import User
from server.utils.phone import proccess_phone_number
from server.utils.credit_transfers import make_payment_transfer
from server.utils.pusher import push_admin_credit_transfer


_ = lambda s: s

class MessageProcessor(object):

    def __init__(self, inbound_phone, inbound_message, message_source = None, provider_message_id = None):

        self.inbound_phone = proccess_phone_number(inbound_phone)
        self.inbound_message = inbound_message.lower()
        self.inbound_user = User.query.filter_by(phone = self.inbound_phone).first()

        self.inbound_transfer_account = self.inbound_user.transfer_account

        self.chatbot_state = self.inbound_user.chatbot_state
        self.provider_message_id = provider_message_id

        self.message_source = message_source

    def process_message(self):

        return_value = self.determine_state()

        return return_value

    def reset_chatbot_state(self):
        self.chatbot_state.transfer_initialised = False
        self.chatbot_state.target_user_id    = None
        self.chatbot_state.transfer_amount      = None
        self.chatbot_state.prev_pin_failures    = 0
        self.chatbot_state.last_accessed        = datetime.datetime.utcnow()

    # def handle_registration_request(self):
    #     split_text = self.inbound_message.split(' ')
    #
    #     first_name = None
    #     last_name = None
    #
    #     try:
    #         first_name = split_text[1]
    #         last_name = split_text[2]
    #     except IndexError:
    #         pass
    #
    #     user = create_transfer_account_user(self.inbound_phone,first_name,last_name,True)
    #
    #     message = _('You have been registered for {}. You have {} {}. Your PIN is {}. To send {} to another phone number type SEND.')\
    #         .format(
    #         app.config['PROGRAM_NAME'],
    #         user.transfer_account.balance / 100,
    #         app.config['CURRENCY_NAME'],
    #         user.transfer_account.pin,
    #         app.config['CURRENCY_NAME']
    #     )
    #
    #     return message

    def handle_no_user_found(self):
        message = _("You are not registered")
        return message

    def handle_fallback(self):

        message = _("Type 'SEND' to send credit, or 'BAL' to view your balance")
        return message

    def handle_use_whatsapp_request(self):

        self.chatbot_state.source_preference = 'WHATSAPP'

        message = _("We will now send future messages using WhatsApp")
        return message

    def handle_use_sms_request(self):

        self.chatbot_state.source_preference = 'SMS'

        message = _("We will now send future messages using SMS")
        return message

    def handle_balance_request(self):

        balance = self.inbound_transfer_account.balance

        message = _('Your balance is {} {}.') \
            .format(balance / 100, current_app.config['CURRENCY_NAME'])

        return message

    def handle_cancel_transfer_request(self):

        self.reset_chatbot_state()
        message = _('Transfer canceled')
        return message

    def handle_insufficient_funds(self):

        self.reset_chatbot_state()
        message = _("Insufficient Funds. Transfer cancelled")

        return message

    def handle_request_amount_to_send(self):

        balance = self.inbound_transfer_account.balance
        message = _("How much credit would you like to send? You balance is {} {}.") \
            .format(balance / 100, current_app.config['CURRENCY_NAME'])

        return message

    def handle_request_target_phone(self):

        message = _('Sending {} {}. Enter recipient phone number.') \
            .format(self.chatbot_state.transfer_amount / 100, current_app.config['CURRENCY_NAME'])

        return message

    def handle_no_valid_phone(self):
        message = _("Please input a valid phone number, or reply 'CANCEL TRANS' to cancel.")

        return message

    def handle_phone_not_registered(self):
        message = _("The phone you are sending to is not registered. Please try again, or reply 'CANCEL TRANS' to cancel.")

        return message

    def handle_request_pin(self):

        target_user = User.query.get(self.chatbot_state.target_user_id)

        message = _('Sending {} {} to {} {}. Enter Pin to confirm.') \
            .format(self.chatbot_state.transfer_amount / 100,
                    current_app.config['CURRENCY_NAME'],
                    target_user.first_name,
                    target_user.last_name
                    )
        return message

    def handle_intermediate_pin_failure(self):

        self.chatbot_state.prev_pin_failures += 1

        message = _("Incorrect pin, please try again, or reply 'CANCEL TRANS' to start over.")
        return message

    def handle_final_pin_failure(self):

        self.reset_chatbot_state()

        message = _('Incorrect pin. Transfer failed.')

        return message

    def handle_transfer_success(self, transfer):

        target_user = User.query.get(self.chatbot_state.target_user_id)

        receiver_message = _('{} {} ({}) has sent you {} {}') \
            .format(
            self.inbound_user.first_name,
            self.inbound_user.last_name,
            self.inbound_phone,
            self.chatbot_state.transfer_amount / 100,
            current_app.config['CURRENCY_NAME']
        )

        # TODO: CREATE RECIPIENT ALERT
        # if target_user.chat_source_preference == 'WHATSAPP' and target_user.phone:
        #
        #     whatsapp_q.put({'phone': target_user.phone, 'message': receiver_message})
        #
        # elif target_user.phone:

        # send_generic_message(target_user.phone, receiver_message)

        self.reset_chatbot_state()

        push_admin_credit_transfer(transfer)

        sender_message = _('Transfer Successful. Your balance is {} {}.') \
            .format(self.inbound_transfer_account.balance / 100, current_app.config['CURRENCY_NAME'])

        return sender_message

    def handle_make_transfer(self):
        target_user = User.query.get(self.chatbot_state.target_user_id)

        transfer = make_payment_transfer(
            self.chatbot_state.transfer_amount,
            self.inbound_user,target_user,
            transfer_mode='SMS')

        # transfer = transfer_credit_via_phone(self.inbound_transfer_account.phone, target_user.phone,
        #                                      self.chatbot_state.transfer_amount)

        return self.handle_transfer_success(transfer)

        # if transfer.get('status') == 'Success':
        #     return self.handle_transfer_success(transfer)
        #
        # self.reset_chatbot_state()
        # return transfer.get('message')

    def determine_state(self):

        if self.inbound_transfer_account is None:
            # This allows users to self-register
            # if _('reg') in self.inbound_message:
            #     return self.handle_registration_request()

            return self.handle_no_user_found()

        if self.inbound_user.chatbot_state is None:
            new_chatbot_state  = ChatbotState()

            db.session.add(new_chatbot_state)

            self.inbound_user.chatbot_state = new_chatbot_state
            self.chatbot_state = new_chatbot_state

        if  self.provider_message_id and self.chatbot_state.provider_message_id == self.provider_message_id:
            print('seen message id {} before, skipping'.format(self.provider_message_id))
            return

        self.chatbot_state.provider_message_id = self.provider_message_id
        # We need to get the previous state into the db ASAP
        # in order to avoid re-running logic multiple times if the provider retries
        db.session.commit()

        time_elapsed = datetime.datetime.utcnow() - self.chatbot_state.last_accessed

        if time_elapsed.seconds > 60*5:
            self.reset_chatbot_state()

        self.chatbot_state.last_accessed = datetime.datetime.utcnow()

        if _('use whatsapp') in self.inbound_message and self.message_source == 'WHATSAPP':
            return self.handle_use_whatsapp_request()

        if _('use sms') in self.inbound_message:
            return self.handle_use_sms_request()

        if _('bal') in self.inbound_message:
            return self.handle_balance_request()

        if _('cancel') in self.inbound_message:
            return self.handle_cancel_transfer_request()

        # No prior settings
        if (self.chatbot_state.target_user_id is None) and (self.chatbot_state.transfer_amount is None):

            if _('send') in self.inbound_message:

                self.chatbot_state.transfer_initialised = True

                split_list = self.inbound_message.split(_('to'))

                # If it does contain 'to', attempt to parse the message using 'to' as the split
                if len(split_list) > 1:

                    return self.check_and_set_amount_and_phone_then_respond(split_list[0], split_list[1])

            #Otherwise parse the entire thing together
                return self.check_and_set_amount_and_phone_then_respond(self.inbound_message, self.inbound_message)

            #If send isn't in the message, but it was in a previous one, just look for credit first

            if self.chatbot_state.transfer_initialised:
                return self.check_and_set_amount_and_phone_then_respond(self.inbound_message)

            #We're missing the 'send' startword, and we haven't seen it in the past, send fallback
            return self.handle_fallback()

        # At least one field missing, so don't check for pin
        if self.chatbot_state.transfer_amount is None or self.chatbot_state.target_user_id is None:

            return self.check_and_set_amount_and_phone_then_respond(self.inbound_message, self.inbound_message)

        # We have everything, check for auth
        if self.chatbot_state.target_user_id:

            if self.inbound_user.verify_password(self.inbound_message):
                return self.handle_make_transfer()

            if self.chatbot_state.prev_pin_failures > 0:

                return self.handle_final_pin_failure()

            return self.handle_intermediate_pin_failure()

        return self.handle_fallback()

    def find_phone_and_credit(self,input_string):
        phone_number = None
        credit_amount = None
        public_serial_number = None

        replaced_list = input_string \
            .replace(';', ' ').replace(',', ' ').replace(':', ' ').replace('(', ' ').replace(')', ' ').strip('!').strip(
            '?')

        stripped_between_numbers = re.sub('(?<=\d) +(?=\d)', '', replaced_list)

        string_list = stripped_between_numbers.split(' ')

        for string in string_list:
            if len(string) == 6 and re.search('v\d{5}',str(string).lower()):
                public_serial_number = string.lower()
                continue

            if len(string) == 8 and re.search('[a-zA-Z]', 'string') is not None:  # It could be an old qr id
                substr = string[1:]
                if substr != substr.lower() and substr != substr.upper():  # There's a mix of upper case and lower case after the first letter
                    public_serial_number = string
                    continue

            try:
                number = float(string)

                if len(string) == 6 and '.' not in string:  # It's probably a new public id
                    public_serial_number = string

                elif len(string) > 7 and ('.' not in string[0:-1]):  # It's probably a phone number

                    if phone_number:  # Oh no there's already a phone number

                        if len(string) > len(phone_number):  # The new one looks more legit
                            phone_number = proccess_phone_number(string)

                    else:
                        phone_number = proccess_phone_number(string)

                else:
                    credit_amount = number

            except ValueError:
                pass

        return {'phone': phone_number, 'credit': credit_amount, 'public_serial_number': public_serial_number}

    def check_and_set_credit_amount(self, text_body):

        credit = self.find_phone_and_credit(text_body).get('credit')

        if credit is None:

            return None

        credit_in_cents = int(float(credit) * 100)

        if self.inbound_transfer_account.balance < credit_in_cents:

            return self.handle_insufficient_funds()

        self.chatbot_state.transfer_amount = credit_in_cents

        return None

    def check_and_set_recipient_phone(self, text_body):

        text_search = self.find_phone_and_credit(text_body)

        target_phone = text_search.get('phone')
        target_public_serial_number = text_search.get('public_serial_number')

        target_user = None

        if target_phone is None and target_public_serial_number is None:
            return None

        if target_phone:
            target_user = User.query.filter_by(phone=target_phone).first()

        if target_user is None and target_public_serial_number:
            target_user = User.query.filter_by(public_serial_number=target_public_serial_number).first()

        if target_user is None:

            return self.handle_phone_not_registered()

        self.chatbot_state.target_user_id = target_user.id

        return None

    def check_and_set_amount_and_phone_then_respond(self, credit_text='', phone_text=''):


        if self.chatbot_state.transfer_amount is None:

            credit_set_response = self.check_and_set_credit_amount(credit_text)

            if credit_set_response is not None:
                return credit_set_response

        if self.chatbot_state.target_user_id is None:

            phone_set_response = self.check_and_set_recipient_phone(phone_text)

            if phone_set_response is not None:
                return phone_set_response

        if self.chatbot_state.transfer_amount is None:
            return self.handle_request_amount_to_send()

        if self.chatbot_state.target_user_id is None:
            return self.handle_request_target_phone()

        # We just need confirmation/auth
        if current_app.config['CHATBOT_REQUIRE_PIN']:
            return self.handle_request_pin()
        else:
            return self.handle_make_transfer()

def bind_fb_psid_to_account(message,psid):

    if message == "bind demo pin 4563":
        transfer_account = User.query.get(5)

        transfer_account.facebook_psid = str(psid)

        db.session.commit()

        return 'Bound to demo account'

    try:

        index_of_use = message.lower().index('use')

        index_of_pin = message.lower().index('pin')

        phone_number = proccess_phone_number(message[index_of_use + 3: index_of_pin])

        pin = str(int(message[index_of_pin + 3:]))

    except:
        return 'Please link to your Sempo account first'

    user = User.query.filter_by(phone=phone_number).first()

    if user is None:

        return 'phone number not registered'

    if user.verify_password(pin):

        return 'wrong pin'

    user.facebook_psid = str(psid)

    db.session.commit()

    return 'Sempo account linked'