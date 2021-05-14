from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView

from server import db
from server.utils.misc import get_parsed_arg_list
from server.utils.auth import requires_auth
from server.models.token import Token, TokenType
from server.schemas import token_schema, tokens_schema

token_blueprint = Blueprint('token', __name__)
from sqlalchemy import func


class TokenAPI(MethodView):

    def get(self):

        symbols = get_parsed_arg_list('symbols', to_lower=True)
        exchange_pairs = get_parsed_arg_list('exchange_pairs', to_lower=True)

        if len(symbols) > 0:
            tokens = Token.query.filter(func.lower(Token.symbol).in_(symbols)).all()
        else:
            tokens = Token.query.all()

        exchange_pair_tokens = Token.query.filter(func.lower(Token.symbol).in_(exchange_pairs)).all()

        tokens_schema.context = {'exchange_pairs': exchange_pair_tokens}

        response_object = {
            'message': 'success',
            'data': {
                'tokens': tokens_schema.dump(tokens).data
            }
        }

        return make_response(jsonify(response_object)), 200

    @requires_auth(allowed_roles={'ADMIN': 'superadmin'})
    def post(self):
        """
        This endpoint is for registering a token with an existing smart contract on the system,
        rather than creating a new contract.
        To create a new token contract, use api/contract/token/.
        """
        post_data = request.get_json()
        name = post_data['name']
        symbol = post_data['symbol']
        decimals = post_data.get('decimals', 18)
        address = post_data.get('address')
        is_reserve = post_data.get('is_reserve', True)
        chain = post_data.get('chain', 'ETHEREUM')

        token = Token.query.filter_by(address=address).first()

        if token:
            response_object = {
                'message': 'Token already exists',
                'data': {
                    'token': token_schema.dump(token).data
                }
            }

            return make_response(jsonify(response_object)), 400

        if not address or not name or not symbol:
            return make_response(jsonify({'message': 'Must include address, name and symbol to create token'})), 400

        token_type = TokenType.RESERVE if is_reserve else TokenType.LIQUID

        token = Token(address=address, name=name, symbol=symbol, token_type=token_type, chain=chain)
        token.decimals = decimals
        db.session.add(token)
        db.session.commit()

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
