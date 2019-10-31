import phonenumbers
import enum
from flask import current_app

from server import twilio_client, messagebird_client, africastalking_client


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


class ChannelType(enum.Enum):
    TWILIO = "tw"
    AFRICAS_TALKING = "at"
    MESSAGEBIRD = "mb"


# just checking by area code may break down one day since multiple countries share the same country codes...
def channel_for_number(phone):
    if phone.startswith("+1"):
        return ChannelType.TWILIO
    if phone.startswith("+254"):
        return ChannelType.AFRICAS_TALKING
    else:
        # what should fallback be?
        return ChannelType.TWILIO


def send_message(to_phone, message):
    if not current_app.config['IS_TEST']:
        channel = channel_for_number(to_phone)
        if channel == ChannelType.TWILIO:
            send_twilio_message(to_phone, message)
        if channel == ChannelType.MESSAGEBIRD:
            send_messagebird_message(to_phone, message)
        if channel == ChannelType.AFRICAS_TALKING:
            send_at_message(to_phone, message)


def send_twilio_message(to_phone, message):
    if to_phone:
        twilio_client.api.account.messages.create(
            to=to_phone,
            from_=current_app.config['TWILIO_PHONE'],
            body=message)


def send_messagebird_message(to_phone, message):
    if to_phone:
        messagebird_client.message_create(current_app.config['MESSAGEBIRD_PHONE'], to_phone, message)


def send_at_message(to_phone, message):
    if to_phone:
        africastalking_client.send(message, [to_phone])
