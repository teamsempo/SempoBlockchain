import re, phonenumbers
from flask import session, current_app
from twilio.twiml.messaging_response import MessagingResponse

from server import twilio_client, messagebird_client


def make_sms_respone(message):
    resp = MessagingResponse()
    resp.message(message)
    return str(resp)


def proccess_phone_number(phone_number, region=None, ignore_region=False):
    """
    Parse any given phone number.
    :param phone_number: int
    :param region: ISO 3166-1 alpha-2 codes
    :param ignore_region: Boolean. True returns original phone
    :return:
    """
    if phone_number is None:
        return None

    if ignore_region:
        return phone_number

    if region is None:
        region = current_app.config['DEFAULT_COUNTRY']

    if not isinstance(phone_number, str):
        try:
            phone_number = str(int(phone_number))

        except ValueError:
            pass

    phone_number_object = phonenumbers.parse(phone_number, region)

    parsed_phone_number = phonenumbers.format_number(phone_number_object, phonenumbers.PhoneNumberFormat.E164)

    return parsed_phone_number


def send_phone_verification_message(to_phone, one_time_code):
    if to_phone:
        reciever_message = 'Your Sempo verification code is: {}'.format(one_time_code)

        send_generic_message(to_phone, reciever_message)


def send_onboarding_message(to_phone, first_name, credits, one_time_code):
    if credits is None:
        credits = 0

    if to_phone:
        receiver_message = '{}, you have been registered for {}. You have {} {}. Your one-time code is {}. ' \
                           'Download Sempo for Android: https://bit.ly/2UVZLqf'\
            .format(
            first_name,
            current_app.config['PROGRAM_NAME'],
            credits,
            current_app.config['CURRENCY_NAME'],
            one_time_code,
            current_app.config['CURRENCY_NAME']
        )

        send_generic_message(to_phone, receiver_message)

def send_intro_message(to_phone, credits, pin):

    if to_phone:
        receiver_message = 'You have been registered for {}. You have {} {}. Your PIN is {}. ' \
                           'To send {} to another phone number type SEND.' \
                .format(
            current_app.config['PROGRAM_NAME'],
            credits/100,
            current_app.config['CURRENCY_NAME'],
            pin,
            current_app.config['CURRENCY_NAME']
        )

        # send_generic_message(to_phone, receiver_message)

def send_secondary_disbursement_message(to_phone, increment_credits, balance):

    if to_phone:
        receiver_message = 'You have been sent an extra {} {}. Your balance is now {} {}.' \
            .format(
            increment_credits / 100,
            current_app.config['CURRENCY_NAME'],
            balance / 100,
            current_app.config['CURRENCY_NAME']
        )

        send_generic_message(to_phone, receiver_message)


def send_generic_message(to_phone, message):
    # todo- add active SMS provider/fallback.
    send_twilio_message(to_phone, message)
    # send_messagebird_message(to_phone, message)

def send_twilio_message(to_phone, message):

    if to_phone:
        twilio_client.api.account.messages.create(
            to=to_phone,
            from_=current_app.config['TWILIO_PHONE'],
            body=message)


def send_messagebird_message(to_phone, message):

    if to_phone:
        msg = messagebird_client.message_create(current_app.config['MESSAGEBIRD_PHONE'], to_phone, message)