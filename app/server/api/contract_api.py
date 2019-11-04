from flask import Blueprint, request, make_response, jsonify, current_app
from flask.views import MethodView

from server import db, bt
from server.utils.auth import requires_auth
from server.models.token import Token
from server.models.exchange import ExchangeContract
from server.schemas import token_schema

deploy_contracts_blueprint = Blueprint('contracts', __name__)


class ContractsAPI(MethodView):

    @requires_auth(allowed_roles={'ADMIN': 'sempoadmin'})
    def post(self):
        # post_data = request.get_json()

        name = 'CIC Test 2'
        symbol = 'CIC2'
        decimals = 18

        reserve_name = 'RESERVE 3'
        reserve_symbol = 'RSV3'

        reserve_ratio_ppm = int(250*10**3)

        deploying_address = current_app.config['MASTER_WALLET_ADDRESS']

        registry_address = bt.deploy_exchange_network(deploying_address)

        reserve_token_address = bt.deploy_and_fund_reserve_token(
            deploying_address=deploying_address,
            name=reserve_name,
            symbol=reserve_symbol,
            fund_amount_wei=1*10**18
        )

        reserve_token = Token(address=reserve_token_address, name=reserve_name, symbol=reserve_symbol)
        reserve_token.decimals = 18
        db.session.add(reserve_token)

        smart_token_result = bt.deploy_smart_token(
            deploying_address=deploying_address,
            name=name, symbol=symbol, decimals=decimals,
            issue_amount_wei=1000,
            contract_registry_address=registry_address,
            reserve_token_address=reserve_token_address,
            reserve_ratio_ppm=reserve_ratio_ppm
        )

        smart_token_address = smart_token_result['smart_token_address']
        converter_address = smart_token_result['converter_address']

        smart_token = Token(address=smart_token_address, name=name, symbol=symbol)
        smart_token.decimals = decimals
        db.session.add(smart_token)

        exchange_contract = ExchangeContract(
            blockchain_address=converter_address,
            contract_registry_blockchain_address=registry_address
        )

        exchange_contract.add_reserve_token(reserve_token)
        exchange_contract.add_token(smart_token, converter_address, reserve_ratio_ppm)

        smart_token_result2 = bt.deploy_smart_token(
            deploying_address=deploying_address,
            name='Goop3', symbol='Goop3', decimals=decimals,
            issue_amount_wei=1000,
            contract_registry_address=registry_address,
            reserve_token_address=reserve_token_address,
            reserve_ratio_ppm=reserve_ratio_ppm
        )

        smart_token_address2 = smart_token_result2['smart_token_address']
        converter_address2 = smart_token_result2['converter_address']

        smart_token2 = Token(address=smart_token_address2, name='Goop2', symbol='Goop2')
        smart_token2.decimals = decimals
        db.session.add(smart_token2)

        exchange_contract.add_token(smart_token2, converter_address2, reserve_ratio_ppm)

        db.session.commit()

        response_object = {
            'message': 'success',
            'data': {
                'reserve_token': {
                    'id': reserve_token.id,
                    'blockchain_address': reserve_token.address,
                },
                'smart_token': {
                    'id': smart_token.id,
                    'blockchain_address': smart_token.address,
                },
                'smart_token_2': {
                    'id': smart_token2.id,
                    'blockchain_address': smart_token2.address,
                },
                'exchange_contract': {
                    'id': exchange_contract.id,
                    'blockchain_address': exchange_contract.blockchain_address
                }
            }
        }

        print(response_object)

        return make_response(jsonify(response_object)), 201


deploy_contracts_blueprint.add_url_rule(
    '/contract/',
    view_func=ContractsAPI.as_view('deploy_contracts_view'),
    methods=['POST']
)
