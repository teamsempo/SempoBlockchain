from flask import Blueprint, request, make_response, jsonify, current_app, g, copy_current_request_context
from flask.views import MethodView
from flask import g

import threading

from server import db, bt
from server.utils.auth import requires_auth, show_all
from server.utils.contract import deploy_cic_token
from server.models.token import Token, TokenType
from server.models.exchange import ExchangeContract
from server.models.organisation import Organisation
from server.schemas import exchange_contract_schema, exchange_contracts_schema, token_schema, tokens_schema

contracts_blueprint = Blueprint('contracts', __name__)


class ExchangeContractAPI(MethodView):

    @requires_auth
    def get(self, exchange_contract_id):

        if exchange_contract_id:
            exchange_contract = ExchangeContract.query.get(exchange_contract_id)

            response_object = {
                'message': 'success',
                'data': {
                    'exchange_contract': exchange_contract_schema.dump(exchange_contract).data
                }
            }

            return make_response(jsonify(response_object)), 201


        exchange_contracts = ExchangeContract.query.all()

        response_object = {
            'message': 'success',
            'data': {
                'exchange_contracts': exchange_contracts_schema.dump(exchange_contracts).data
            }
        }

        return make_response(jsonify(response_object)), 201

    @requires_auth(allowed_roles={'ADMIN': 'sempoadmin'})
    def post(self, exchange_contract_id):
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
        db.session.commit()

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
    def get(self, token_id):
        if token_id:
            token = Token.query.get(token_id)

            response_object = {
                'message': 'success',
                'data': {
                    'token': token_schema.dump(token).data
                }
            }

            return make_response(jsonify(response_object)), 201

        tokens = Token.query.all()

        response_object = {
            'message': 'success',
            'data': {
                'tokens': tokens_schema.dump(tokens).data
            }
        }

        return make_response(jsonify(response_object)), 201

    @requires_auth(allowed_roles={'ADMIN': 'sempoadmin'})
    def post(self, token_id):
        """
        This endpoint is for creating a new contract,
        rather registering a token with an existing smart contract on the system.
        To create a new token contract, use api/token/.
        """
        post_data = request.get_json()

        # We use almost the exact same flow as a subflow of create organisation, so create a helper function
        response_object, response_code = deploy_cic_token(post_data)

        return make_response(jsonify(response_object)), response_code


class ReserveTokenAPI(MethodView):

    @requires_auth(allowed_roles={'ADMIN': 'sempoadmin'})
    def post(self):
        """
        Dev function for creating a reserve token AFTER master organisation setup, and then binding to master org
        """
        post_data = request.get_json()

        name = post_data['name']
        symbol = post_data['symbol']
        fund_amount_wei = post_data['fund_amount_wei']

        deploying_address = g.user.primary_blockchain_address
        if not Organisation.query.filter_by(is_master=True).first():
            response_object = {
                    'message': 'Master organisation not found'
                }

            return make_response(jsonify(response_object)), 400

        token = Token(name=name, symbol=symbol, token_type=TokenType.RESERVE)
        db.session.add(token)
        db.session.flush()

        deploy_data = dict(
            deploying_address=deploying_address,
            name=name, symbol=symbol, fund_amount_wei=fund_amount_wei,
        )

        @copy_current_request_context
        def deploy(_deploy_data, _token_id):
            # TODO: Work out why execution options doesn't work
            g.show_all = True
            reserve_token_address = bt.deploy_and_fund_reserve_token(**_deploy_data)

            _token = Token.query.get(_token_id)
            _token.address = reserve_token_address

            _token.get_decimals()

            master_org = Organisation.query.filter_by(is_master=True).execution_options(show_all=True).first()
            master_org.bind_token(_token)
            master_org.org_level_transfer_account.set_balance_offset(int(_deploy_data['fund_amount_wei'] / 1e16))
            db.session.commit()

        t = threading.Thread(target=deploy,
                             args=(deploy_data, token.id))
        t.daemon = True
        t.start()

        response_object = {
            'message': 'success',
            'data': {
                'reserve_token_id': token.id
            }
        }

        return make_response(jsonify(response_object)), 201


contracts_blueprint.add_url_rule(
    '/contract/exchange/',
    view_func=ExchangeContractAPI.as_view('contract_view'),
    methods=['POST', 'GET'],
    defaults={'exchange_contract_id': None}

)

contracts_blueprint.add_url_rule(
    '/contract/exchange/<int:exchange_contract_id>/',
    view_func=ExchangeContractAPI.as_view('single_contract_view'),
    methods=['POST', 'GET']
)


contracts_blueprint.add_url_rule(
    '/contract/token/',
    view_func=TokenAPI.as_view('token_view'),
    methods=['POST', 'GET'],
    defaults={'token_id': None}
)

contracts_blueprint.add_url_rule(
    '/contract/token/<int:token_id>/',
    view_func=TokenAPI.as_view('single_token_view'),
    methods=['GET']
)

contracts_blueprint.add_url_rule(
    '/contract/token/reserve/',
    view_func=ReserveTokenAPI.as_view('reserve_token_view'),
    methods=['POST']
)

