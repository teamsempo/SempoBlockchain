from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView

from server import db
from server.utils.auth import requires_auth
from server.models.token import Token
from server.models.exchange import ExchangeContract
from server.schemas import token_schema, tokens_schema

token_blueprint = Blueprint('token', __name__)

class TokenAPI(MethodView):

    @requires_auth(allowed_basic_auth_types=['internal'])
    def get(self):

        tokens = Token.query.all()

        response_object = {
            'message': 'success',
            'data': {
                'tokens': tokens_schema.dump(tokens).data
            }
        }

        return make_response(jsonify(response_object)), 200


    @requires_auth(allowed_roles={'ADMIN': 'sempoadmin'})
    def post(self):
        post_data = request.get_json()

        address = post_data['address']
        name = post_data['name']
        symbol = post_data['symbol']

        token = Token.query.filter_by(address=address).first()

        if token:
            response_object = {
                'message': 'Token already exists',
                'data': {
                    'token': token_schema.dump(token).data
                }
            }

            return make_response(jsonify(response_object)), 400

        token = Token(address=address, name=name, symbol=symbol)

        db.session.add(token)
        db.session.commit()

        response_object = {
            'message': 'success',
            'data': {
                'token': {
                    'id': token.id
                }
            }
        }

        return make_response(jsonify(response_object)), 201


class TokenExchangeContractAPI(MethodView):

    @requires_auth(allowed_basic_auth_types=['internal'])
    def put(self, token_id):

        put_data = request.get_json()
        exchange_contract_id = put_data.get('exchange_contract_id')

        # Even though it's non-standard, allow specifying exchange contract by address
        # Because it's often way easier to get hold of than the contract id
        exchange_contract_address = put_data.get('exchange_contract_address')


        token = Token.query.get(token_id)

        if token is None:
            return make_response(jsonify(
                {'message': 'No Token found for ID: {}'.format(token_id)}))


        if exchange_contract_address and exchange_contract_id:
            return make_response(jsonify(
                {'message': 'Must ONLY specify one of exchange contract id or address'}))

        if exchange_contract_id:
            exchange_contract = ExchangeContract.query.get(exchange_contract_id)

        elif exchange_contract_address:
            exchange_contract = ExchangeContract.query.filter_by(blockchain_address = exchange_contract_address).first()

        else:
            return make_response(jsonify(
                {'message': 'Must specify one of exchange contract id or address'}))

        if exchange_contract is None:
            return make_response(jsonify(
                {'message': 'No Exchange Contract found for ID: {}'.format(exchange_contract_id)}))

        token.exchange_contracts.append(exchange_contract)

        db.session.commit()

        response_object = {
            'message': 'success',
        }

        return make_response(jsonify(response_object)), 200


token_blueprint.add_url_rule(
    '/token/',
    view_func=TokenAPI.as_view('token_view'),
    methods=['POST', 'GET']
)

token_blueprint.add_url_rule(
    '/token/<int:token_id>/exchange_contracts',
    view_func=TokenExchangeContractAPI.as_view('token_exchange_contract_view'),
    methods=['PUT']
)