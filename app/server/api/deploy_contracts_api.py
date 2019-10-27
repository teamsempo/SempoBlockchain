from flask import Blueprint, request, make_response, jsonify, current_app
from flask.views import MethodView

from server import db
from server.utils.auth import requires_auth
from server.models.token import Token
from server.models.exchange import ExchangeContract
from server.schemas import token_schema
from server.utils.blockchain_tasks import deploy_reserve_network, deploy_and_fund_reserve_token, deploy_smart_token


deploy_contracts_blueprint = Blueprint('deploy_contracts', __name__)


class DeployContractsAPI(MethodView):

    @requires_auth(allowed_roles={'ADMIN': 'sempoadmin'})
    def post(self):
        # post_data = request.get_json()

        name = 'CIC Test'
        symbol = 'CIC1'
        decimals = 18

        deploying_address = current_app.config['MASTER_WALLET_ADDRESS']

        registry_address = deploy_reserve_network(deploying_address)

        reserve_token_address = deploy_and_fund_reserve_token(
            deploying_address=deploying_address,
            fund_amount_wei=10000000
        )

        reserve_token = Token(address=reserve_token_address, name='RESERVE 1', symbol='R!1')
        reserve_token.decimals = 18
        db.session.add(reserve_token)

        smart_token_result = deploy_smart_token(
            deploying_address=deploying_address,
            name=name, symbol=symbol, decimals=decimals,
            issue_amount_wei=10,
            contract_registry_address=registry_address,
            reserve_token_address=reserve_token_address,
            reserve_ratio_ppm=int(500*10**3)
        )

        smart_token_address = smart_token_result['smart_token_address']
        converter_address = smart_token_result['converter_address']

        smart_token = Token(address=smart_token_address, name=name, symbol=symbol)
        smart_token.decimals = decimals
        db.session.add(smart_token)

        exchange_contract = ExchangeContract(blockchain_address=converter_address)
        exchange_contract.add_reserve_token(reserve_token)
        exchange_contract.add_token(smart_token)

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
                'exchange_contract': {
                    'id': exchange_contract.id,
                    'blockchain_address': exchange_contract.blockchain_address
                }
            }
        }

        return make_response(jsonify(response_object)), 201


deploy_contracts_blueprint.add_url_rule(
    '/contracts/',
    view_func=DeployContractsAPI.as_view('deploy_contracts_view'),
    methods=['POST']
)
