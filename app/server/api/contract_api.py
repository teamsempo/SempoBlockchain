from flask import Blueprint, request, make_response, jsonify, current_app, g, copy_current_request_context
from flask.views import MethodView
import threading

from server import db, bt
from server.utils.auth import requires_auth
from server.models.token import Token
from server.models.exchange import ExchangeContract
from server.schemas import exchange_contract_schema, exchange_contracts_schema, token_schema, tokens_schema

contracts_blueprint = Blueprint('contracts', __name__)


class ExchangeContractAPI(MethodView):

    @requires_auth
    def get(self):

        exchange_contracts = ExchangeContract.query.all()

        response_object = {
            'message': 'success',
            'data': {
                'exchange_contracts': exchange_contracts_schema.dump(exchange_contracts).data
            }
        }

        return make_response(jsonify(response_object)), 201

    @requires_auth(allowed_roles={'ADMIN': 'sempoadmin'})
    def post(self):
        post_data = request.get_json()

        reserve_token_id = post_data['reserve_token_id']

        deploying_address = g.user.transfer_account.blockchain_address

        reserve_token = Token.query.get(reserve_token_id)

        if not reserve_token:
            response_object = {
                'message': f'Reserve token not found for ID {reserve_token}',
            }

            return make_response(jsonify(response_object)), 404

        exchange_contract = ExchangeContract()

        exchange_contract.add_reserve_token(reserve_token)
        db.session.add(exchange_contract)
        db.session.flush()

        exchange_contract_id = exchange_contract.id

        @copy_current_request_context
        def deploy(_deploying_address, _exchange_contract_id):
            contract_registry_address = bt.deploy_exchange_network(_deploying_address)

            _exchange_contract = ExchangeContract.query.get(_exchange_contract_id)
            _exchange_contract.contract_registry_blockchain_address = contract_registry_address

            db.session.commit()

        t = threading.Thread(target=deploy,
                             args=(deploying_address, exchange_contract_id))
        t.daemon = True
        t.start()

        response_object = {
            'message': 'success',
            'data': {
                'exchange_contract': exchange_contract_schema.dump(exchange_contract).data
            }
        }

        return make_response(jsonify(response_object)), 201


class TokenAPI(MethodView):

    @requires_auth
    def get(self):

        tokens = Token.query.all()

        response_object = {
            'message': 'success',
            'data': {
                'tokens': tokens_schema.dump(tokens).data
            }
        }

        return make_response(jsonify(response_object)), 201

    @requires_auth(allowed_roles={'ADMIN': 'sempoadmin'})
    def post(self):
        """
        This endpoint is for creating a new contract,
        rather registering a token with an existing smart contract on the system.
        To create a new token contract, use api/token/.
        """
        post_data = request.get_json()

        name = post_data['name']
        symbol = post_data['symbol']
        decimals = post_data.get('decimals', 18)

        issue_amount_wei = post_data['issue_amount_wei']
        reserve_deposit_wei = post_data['reserve_deposit_wei']

        exchange_contract_id = post_data['exchange_contract_id']
        reserve_ratio_ppm = post_data.get('reserve_ratio_ppm', 250000)

        deploying_address = g.user.transfer_account.blockchain_address

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

        balance_wei = bt.get_wallet_balance(deploying_address, exchange_contract.reserve_token)

        if balance_wei < reserve_deposit_wei:
            response_object = {
                'message': f'Insufficient reserve funds (balance in wei: {balance_wei}'
            }

            return make_response(jsonify(response_object)), 400

        token = Token(name=name, symbol=symbol)
        db.session.add(token)
        db.session.flush()

        deploy_data = dict(
            deploying_address=deploying_address,
            name=name, symbol=symbol, decimals=decimals,
            reserve_deposit_wei=reserve_deposit_wei,
            issue_amount_wei=issue_amount_wei,
            contract_registry_address=exchange_contract.contract_registry_blockchain_address,
            reserve_token_address=exchange_contract.reserve_token.address,
            reserve_ratio_ppm=reserve_ratio_ppm
        )

        @copy_current_request_context
        def deploy(_deploy_data, _token_id, _exchange_contract_id):
            smart_token_result = bt.deploy_smart_token(**_deploy_data)

            address = smart_token_result['smart_token_address']
            subexchange_address = smart_token_result['subexchange_address']

            _token = Token.query.get(_token_id)
            _token.address = address

            _exchange_contract = ExchangeContract.query.get(_exchange_contract_id)

            _exchange_contract.add_token(_token, subexchange_address, reserve_ratio_ppm)

            db.session.commit()

        t = threading.Thread(target=deploy,
                             args=(deploy_data, token.id, exchange_contract_id))
        t.daemon = True
        t.start()

        response_object = {
            'message': 'success',
            'data': {
                'token_id': token.id
            }
        }

        return make_response(jsonify(response_object)), 201


contracts_blueprint.add_url_rule(
    '/contract/exchange/',
    view_func=ExchangeContractAPI.as_view('contracts_view'),
    methods=['POST', 'GET']
)

contracts_blueprint.add_url_rule(
    '/contract/token/',
    view_func=TokenAPI.as_view('token_view'),
    methods=['POST', 'GET']
)
