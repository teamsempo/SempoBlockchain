from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView
from server.models import TransferCard
from server.utils.auth import requires_auth
from server.schemas import transfer_cards_schema
from server import db
import re

transfer_cards_blueprint = Blueprint('transfer_cards', __name__)


class TransferCardAPI(MethodView):
    @requires_auth
    def get(self):

        transfer_cards = TransferCard.query.all()

        response_object = {
            'message': 'Successfully loaded transfer_cards',
            'data': {'transfer_cards': transfer_cards_schema.dump(transfer_cards).data}
        }

        return make_response(jsonify(response_object)), 200

    @requires_auth
    def post(self):
        post_data = request.get_json()

        public_serial_number = post_data.get('public_serial_number')
        nfc_serial_number = post_data.get('nfc_serial_number')

        if not public_serial_number or not nfc_serial_number:
            response_object = {
                'message': 'Missing Data',
            }

            return make_response(jsonify(response_object)), 400

        public_serial_number = re.sub(r'[\t\n\r]', '', public_serial_number)


        if TransferCard.query.filter_by(public_serial_number=public_serial_number).first():
            response_object = {
                'message': 'Public Serial Number already used',
            }

            return make_response(jsonify(response_object)), 400

        if TransferCard.query.filter_by(nfc_serial_number=nfc_serial_number).first():
            response_object = {
                'message': 'NFC Serial Number already used',
            }

            return make_response(jsonify(response_object)), 400

        transfer_card = TransferCard(nfc_serial_number=nfc_serial_number, public_serial_number=public_serial_number)

        db.session.add(transfer_card)
        db.session.commit()

        response_object = {
            'status': 'success',
        }

        return make_response(jsonify(response_object)), 201

transfer_cards_blueprint.add_url_rule(
    '/transfer_cards/',
    view_func=TransferCardAPI.as_view('transfer_card_view'),
    methods=['GET', 'POST']
)

