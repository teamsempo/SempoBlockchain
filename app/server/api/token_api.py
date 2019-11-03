from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView

from server import db
from server.utils.auth import requires_auth
from server.models.token import Token
from server.models.exchange import ExchangeContract
from server.schemas import token_schema, tokens_schema
from server.utils.blockchain_tasks import (
    deploy_smart_token
)

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

        issue_amount_wei = 1000
        post_data = request.get_json()

        name = post_data['name']
        symbol = post_data['symbol']
        decimals = post_data.get('decimals', 18)
        address = post_data.get('address')

        deploy_smart_token_contract = post_data['deploy_smart_token_contract']
        exchange_contract_id = post_data.get('exchange_contract_id')
        reserve_ratio_ppm = post_data.get('reserve_ratio_ppm', 250000)

        token = Token.query.filter_by(address=address).first()

        if token:
            response_object = {
                'message': 'Token already exists',
                'data': {
                    'token': token_schema.dump(token).data
                }
            }

            return make_response(jsonify(response_object)), 400

        if deploy_smart_token_contract:

            deploying_address = g.user.transfer_account.blockchain_address

            if address:
                response_object = {
                    'message': "Must not supply address if deploying smart token"
                }

                return make_response(jsonify(response_object)), 400

            if not exchange_contract_id:
                response_object = {
                    'message': 'Must supply exchange contract id if deploying smart token contract'
                }

                return make_response(jsonify(response_object)), 400

            exchange_contract = ExchangeContract.query.get(exchange_contract_id)

            if not exchange_contract:
                response_object = {
                    'message': 'Exchange contract not found for id {}'.format(exchange_contract_id)
                }

                return make_response(jsonify(response_object)), 400

            smart_token_result = deploy_smart_token(
                deploying_address=deploying_address,
                name=name, symbol=symbol, decimals=decimals,
                issue_amount_wei=issue_amount_wei,
                contract_registry_address=exchange_contract.contract_registry_blockchain_address,
                reserve_token_address=exchange_contract.reserve_token.address,
                reserve_ratio_ppm=reserve_ratio_ppm
            )

            address = smart_token_result['smart_token_address']
            subexchange_address = smart_token_result['subexchange_address']

        token = Token(address=address, name=name, symbol=symbol)
        db.session.add(token)
        db.session.commit()

        if deploy_smart_token_contract:

            exchange_contract.add_token(token, subexchange_address, reserve_ratio_ppm)

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
            exchange_contract = ExchangeContract.query.filter_by(blockchain_address=exchange_contract_address).first()

        else:
            return make_response(jsonify(
                {'message': 'Must specify one of exchange contract id or address'}))

        if exchange_contract is None:
            return make_response(jsonify(
                {'message': 'No Exchange Contract found for ID: {}'.format(exchange_contract_id)}))

        exchange_contract.add_token(token)

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