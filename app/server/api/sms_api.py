from flask import Blueprint, request, make_response, jsonify, g, session
from flask.views import MethodView
from flask import current_app

import requests
import base64
import hmac
import hashlib

from server import db
from server.utils.chatbot_controller import MessageProcessor, bind_fb_psid_to_account
from server.utils.phone import make_sms_respone, send_messagebird_message
from server.models import TransferAccount

sms_blueprint = Blueprint('sms', __name__)


class ProcessSMSAPI(MethodView):

    def post(self):
        inbound_phone = request.values.get('From')
        message_body = request.values.get('Body')

        processor = MessageProcessor(inbound_phone, message_body, message_source='SMS')

        reply = processor.process_message()

        return make_sms_respone(reply)


class ProcessFBChatAPI(MethodView):

    def post(self):

        body = request.json

        if body['object'] == 'page':

            for entry in body['entry']:
                webhook_event = entry['messaging'][0]

                print(webhook_event)

                sender_psid = webhook_event['sender']['id']
                inbound_message_text = webhook_event['message']['text']

                transfer_account = TransferAccount.query.filter_by(facebook_psid = str(sender_psid)).first()

                if transfer_account is None:
                    response_text = bind_fb_psid_to_account(inbound_message_text, sender_psid)
                else:

                    inbound_phone= transfer_account.phone

                    processor = MessageProcessor(inbound_phone, inbound_message_text, message_source='SMS')

                    response_text = processor.process_message()

                response = {
                    "text": response_text
                }

                self.call_send_api(sender_psid,response)

            response_object = {
                'status': 'success'
            }

            return make_response(jsonify(response_object)), 200

        response_object = {
            'status': 'fail'
        }

        return make_response(jsonify(response_object)), 404

    def call_send_api(self,sender_psid,response):

        request_body = {
            'recipient': {
                'id': sender_psid
            },
            "message": response
        }

        params = {'access_token': current_app.config['FACEBOOK_TOKEN']}

        r = requests.post("https://graph.facebook.com/v2.6/me/messages", params = params, json=request_body)

        if r.reason != 'OK':
            print(r.text)


    def get(self):

        VERIFY_TOKEN = current_app.config['FACEBOOK_VERIFY_TOKEN']

        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if (mode and token):
            if (mode == 'subscribe' and token == VERIFY_TOKEN):
                print('FB_WEBHOOK_VERIFIED')


            return make_response(challenge), 201

        response_object = {
            'status': 'fail',
        }

        return make_response(jsonify(response_object)), 403


class ProcessMessageBirdConvoAPI(MethodView):


    def call_send_messagebird_api(self,conversation_id,response):

        headers = {
            'Authorization': 'AccessKey ' + current_app.config['MESSAGEBIRD_KEY'],
            'Content-Type': 'application/json',
        }

        request_body = {
            "type": "text",
            "content": {
                "text": response
            }
        }

        response = requests.post(
            'https://conversations.messagebird.com/v1/conversations/{}/messages'.format(conversation_id),
            headers=headers, json=request_body)

        if response.reason != 'OK':
            print(response.text)


    def post(self):

        body = request.json

        inbound_message_text = body['message']['content']['text']

        contactID = body['conversation']['contactId']

        conversation_id = body['conversation']['id']

        direction = body['message']['direction']

        if direction == 'sent':
            response_object = {
                'status': 'success'
            }

            return make_response(jsonify(response_object)), 200


        transfer_account = TransferAccount.query.filter_by(facebook_psid = str(contactID)).first()

        if transfer_account is None:
            response_text = bind_fb_psid_to_account(inbound_message_text, contactID)
        else:

            inbound_phone = transfer_account.phone

            processor = MessageProcessor(inbound_phone, inbound_message_text, message_source='SMS')

            response_text = processor.process_message()

        self.call_send_messagebird_api(conversation_id,response_text)

        response_object = {
            'status': 'success'
        }

        return make_response(jsonify(response_object)), 200

class ProcessMessageBirdSMSAPI(MethodView):

    def post(self):

        if not verify_messagebird_signature():
            return make_response('Invalid Signature'), 401

        body = request.json

        inbound_message_text = body.get('body')

        provider_message_id = body.get('id')

        if inbound_message_text is None:
            return make_response('OK'), 200

        originator = body['originator']

        # TODO: WTF DOES THIS EVEN DO?
        if body['originator'] == '61488826088':

            return make_response('OK'), 200


        phone = '+' + originator

        processor = MessageProcessor(phone, inbound_message_text, message_source='SMS', provider_message_id = provider_message_id)

        response_text = processor.process_message()

        db.session.commit()

        if response_text:
            send_messagebird_message(originator,response_text)

        return make_response('OK'), 200


def verify_messagebird_signature():
    request_signature = base64.b64decode(request.headers.environ['HTTP_MESSAGEBIRD_SIGNATURE'])
    request_timestamp = request.headers.environ['HTTP_MESSAGEBIRD_REQUEST_TIMESTAMP']
    request_query_string = request.query_string
    request_body = request.data

    string_to_check = (request_timestamp.encode()
                       + '\n'.encode()
                       + request_query_string
                       + '\n'.encode()
                       + hashlib.sha256(request_body).digest())

    signature = hmac.new('JPa8Z9i7rVYMtKtURcFiGj0B48sPCNby'.encode(), string_to_check, hashlib.sha256).digest()

    #TODO: MAKE THIS COMPARISON CONSTANT TIME
    return signature == request_signature



sms_blueprint.add_url_rule(
    '/sms/',
    view_func=ProcessSMSAPI.as_view('sms_view'),
    methods=['POST','GET']
)

sms_blueprint.add_url_rule(
    '/facebook/',
    view_func=ProcessFBChatAPI.as_view('fb_view'),
    methods=['POST','GET']
)

sms_blueprint.add_url_rule(
    '/messagebird/conversations/',
    view_func=ProcessMessageBirdConvoAPI.as_view('messagebird_convo_view'),
    methods=['POST','GET']
)

sms_blueprint.add_url_rule(
    '/messagebird/sms/',
    view_func=ProcessMessageBirdSMSAPI.as_view('messagebird_sms_view'),
    methods=['POST','GET']
)




