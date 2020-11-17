from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView
from server.models.transfer_card import TransferCard
from server.models.utils import paginate_query
from server.utils.auth import requires_auth
from server.schemas import transfer_cards_schema
from server import db
import re

transfer_cards_blueprint = Blueprint('transfer_cards', __name__)


class TransferCardAPI(MethodView):
    @requires_auth
    def get(self):
        """
        Get a list of the transfer cards on the system.
        :arg only_bound: only return cards that have transfer accounts bound to them.
        :arg shard: Get only transfer cards within the radius defined by org parameter. Distance is in kilometers
        Prevents returning a list of 100000 cards and overwhelming low power android phones. Defaults true.
        :return:
        """
        shard_param = request.args.get('shard', 'true').lower()
        shard_distance = g.active_organisation.card_shard_distance

        shard = True
        if ((shard_param == 'false') or (not shard_distance)) or (g.user.lat == None and g.user.lng == None):
            shard = False

        if shard:
            nearby_users_filter = g.user.users_within_radius_filter(shard_distance)

            query = TransferCard.query.join(TransferCard.user).filter(nearby_users_filter)

        else:
            only_bound = request.args.get('only_bound', 'true').lower() == 'true' #defaults true

            if only_bound:
                query = TransferCard.query.filter(TransferCard.transfer_account_id != None)
            else:
                query = TransferCard.query

        transfer_cards,  total_items, total_pages, new_last_fetched = paginate_query(query, TransferCard.updated)

        response_object = {
            'message': 'Successfully loaded transfer_cards',
            'data': {'transfer_cards': transfer_cards_schema.dump(transfer_cards).data},
            'last_fetched': new_last_fetched
        }

        return make_response(jsonify(response_object)), 200

    @requires_auth(allowed_basic_auth_types=('external',))
    def post(self):
        post_data = request.get_json()

        public_serial_number = post_data.get('public_serial_number')
        nfc_serial_number = post_data.get('nfc_serial_number')

        if not public_serial_number or not nfc_serial_number:
            response_object = {
                'message': 'Missing Data',
            }

            return make_response(jsonify(response_object)), 400

        # serial numbers are case insensitive
        public_serial_number = re.sub(r'[\t\n\r]', '', str(public_serial_number)).upper()
        nfc_serial_number = nfc_serial_number.upper()

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

