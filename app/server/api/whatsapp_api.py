from flask import Blueprint, request, make_response, jsonify, g, session
from flask.views import MethodView

from server import basic_auth
from server.utils.chatbot_controller import MessageProcessor
from server.utils.auth import requires_auth

whatsapp_blueprint = Blueprint('whatsapp', __name__)

class ProcessWhatsAppAPI(MethodView):

    @requires_auth(allowed_basic_auth_types=('internal'))
    def post(self):
        post_data = request.get_json()

        inbound_phone = post_data.get('username')
        message_body = post_data.get('text').lower()

        processor = MessageProcessor(inbound_phone, message_body, message_source='WHATSAPP')

        reply = processor.process_message()

        response_object = {
            'status': 'success',
            'reply': reply,
        }

        return make_response(jsonify(response_object)), 201


whatsapp_blueprint.add_url_rule(
    '/whatsapp/',
    view_func=ProcessWhatsAppAPI.as_view('whatsapp_view'),
    methods=['POST','GET']
)
