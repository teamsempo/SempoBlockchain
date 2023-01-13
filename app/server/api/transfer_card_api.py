from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView
from server.models.transfer_card import TransferCard
from server.models.utils import paginate_query
from server.utils.auth import requires_auth
from server.schemas import transfer_cards_schema, transfer_card_schema
from server import db
import re

transfer_cards_blueprint = Blueprint('transfer_cards', __name__)


class TransferCardAPI(MethodView):
    @requires_auth
    def get(self, nfc_serial_number, public_serial_number):
        """
        Get a list of the transfer cards on the system.
        :arg only_bound: only return cards that have transfer accounts bound to them.
        :arg shard: Get only transfer cards within the radius defined by org parameter. Distance is in kilometers
        Prevents returning a list of 100000 cards and overwhelming low power android phones. Defaults true.
        :arg nfc_serial_number: get a card according to its nfc serial number
        :return:
        """
        shard_param = request.args.get('shard', 'true').lower()
        shard_distance = g.active_organisation.card_shard_distance

        if nfc_serial_number:
            #     We're looking for a single card
            nfc_serial_number = nfc_serial_number.replace(':', '')
            card = (
                TransferCard.query
                    .filter(TransferCard.transfer_account_id != None)
                    .filter(TransferCard.nfc_serial_number == nfc_serial_number.upper())
                    .first()
            )

            if not card:
                response_object = {
                    'message': 'Card not found',
                }

                return make_response(jsonify(response_object)), 404

            response_object = {
                'message': 'Successfully loaded transfer_card',
                'data': {'transfer_card': transfer_card_schema.dump(card).data},
            }

            return make_response(jsonify(response_object)), 200


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
            'items': total_items,
            'pages': total_pages,
            'last_fetched': new_last_fetched
        }

        return make_response(jsonify(response_object)), 200

    @requires_auth(allowed_basic_auth_types=('external',))
    def post(self, nfc_serial_number, public_serial_number):
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
        nfc_serial_number = nfc_serial_number.upper().replace(':', '')

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

    @requires_auth(allowed_roles={'ADMIN': 'sempoadmin'})
    def put(self, public_serial_number, nfc_serial_number):
        data = request.get_json()

        amount_offset = data.get('amount_offset')

        disable = data.get('disable', False)

        if nfc_serial_number:
            nfc_serial_number = nfc_serial_number.replace(':', '')
            transfer_card = TransferCard.query.filter_by(nfc_serial_number=nfc_serial_number).first()
        else:
            transfer_card = TransferCard.query.filter_by(public_serial_number=public_serial_number).first()

        if not transfer_card:
            response_object = {
                'message': 'Card not found',
            }
            return make_response(jsonify(response_object)), 404

        if disable:
            if transfer_card.is_disabled:
                response_object = {
                    'message': 'Card card already disabled',
                }
                return make_response(jsonify(response_object)), 400

            transfer_card.disable()

        if amount_offset:

            if not transfer_card.transfer_account:
                response_object = {
                    'message': f'Card {transfer_card.id} must be bound to at transfer account to modify offset',
                }
                return make_response(jsonify(response_object)), 400

            transfer_card.amount_offset = amount_offset

            db.session.commit()

        response_object = {
            'message': 'Updated transfer card ',
        }
        return make_response(jsonify(response_object)), 200



transfer_cards_blueprint.add_url_rule(
    '/transfer_cards/',
    view_func=TransferCardAPI.as_view('transfer_card_view'),
    methods=['GET', 'POST'],
    defaults={'nfc_serial_number': None, 'public_serial_number': None}
)

transfer_cards_blueprint.add_url_rule(
    '/transfer_cards/nfc_serial_number/<nfc_serial_number>',
    view_func=TransferCardAPI.as_view('nfc_sn_referenced_transfer_card_view'),
    methods=['GET', 'PUT'],
    defaults={'public_serial_number': None}
)

transfer_cards_blueprint.add_url_rule(
    '/transfer_cards/public_serial_number/<public_serial_number>/',
    view_func=TransferCardAPI.as_view('public_sn_referenced_transfer_card_view'),
    methods=['PUT'],
    defaults={'nfc_serial_number': None}
)
