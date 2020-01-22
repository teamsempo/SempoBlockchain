import phonenumbers
import enum
from flask import current_app
import server

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
        # TODO(org): add an org level default
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


class MessageProcessor(object):
    def __init__(self, twilio_client, messagebird_client, africastalking_client):
        self.twilio_client = twilio_client
        self.messagebird_client = messagebird_client
        self.africastalking_client = africastalking_client

    # just checking by area code may break down one day since multiple countries share the same country codes...
    def channel_for_number(cls, phone):
        if phone.startswith("+1"):
            return ChannelType.TWILIO
        if phone.startswith("+254"):
            return ChannelType.AFRICAS_TALKING
        else:
            # what should fallback be?
            return ChannelType.TWILIO

    def send_message(self, to_phone, message):
        if current_app.config['IS_TEST'] or current_app.config['IS_PRODUCTION']:
            channel = self.channel_for_number(to_phone)
            print(f'Sending SMS via {channel}')
            if channel == ChannelType.TWILIO:
                self._send_twilio_message(to_phone, message)
            if channel == ChannelType.MESSAGEBIRD:
                self._send_messagebird_message(to_phone, message)
            if channel == ChannelType.AFRICAS_TALKING:
                self._send_at_message(to_phone, message)
        else:
            print(f'"IS NOT PRODUCTION", not sending SMS:\n{message}')

    def _send_twilio_message(self, to_phone, message):
        if to_phone:
            self.twilio_client.api.account.messages.create(
                to=to_phone,
                from_=current_app.config['TWILIO_PHONE'],
                body=message)

    def _send_messagebird_message(self, to_phone, message):
        if to_phone:
            self.messagebird_client.message_create(current_app.config['MESSAGEBIRD_PHONE'], to_phone, message)

    def _send_at_message(self, to_phone, message):
        if to_phone:

            # First try with custom sender Id
            resp = self.africastalking_client.send(
                message,
                [to_phone],
                sender_id=current_app.config.get('AT_SENDER_ID', None)
            )

            # If that fails, fallback to no sender ID
            if resp['SMSMessageData']['Message'] == 'InvalidSenderId':
                server.sentry.captureMessage("InvalidSenderId {}".format(current_app.config.get('AT_SENDER_ID', None))) # CHANGE

                resp = self.africastalking_client.send(
                    message,
                    [to_phone])
