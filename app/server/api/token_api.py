from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView

from server import db, bt
from server.utils.auth import requires_auth
from server.models.token import Token, TokenType
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
        """
        This endpoint is for registering a token with an existing smart contract on the system,
        rather than creating a new contract.
        To create a new token contract, use api/contract/token/.
        """
        # TODO: Requires tests
        post_data = request.get_json()
        name = post_data['name']
        symbol = post_data['symbol']
        decimals = post_data.get('decimals', 18)
        address = post_data.get('address')
        is_reserve = post_data.get('is_reserve', True)

        token = Token.query.filter_by(address=address).first()

        if token:
            response_object = {
                'message': 'Token already exists',
                'data': {
                    'token': token_schema.dump(token).data
                }
            }

            return make_response(jsonify(response_object)), 400

        token_type = TokenType.RESERVE if is_reserve else TokenType.LIQUID

        token = Token(address=address, name=name, symbol=symbol, decimals=decimals, token_type=token_type)
        db.session.add(token)

        response_object = {
            'message': 'success',
            'data': {
                'token': token_schema.dump(token).data
            }
        }

        return make_response(jsonify(response_object)), 201


token_blueprint.add_url_rule(
    '/token/',
    view_func=TokenAPI.as_view('token_view'),
    methods=['POST', 'GET']
)
