from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView

from server import db
from server.utils.auth import requires_auth
from server.models.token import Token
from server.models.exchange import ExchangeContract
from server.schemas import token_schema, tokens_schema

exchange_blueprint = Blueprint('exchange', __name__)

# Not sure if we actually need this

# class ExchangeContractTokenAPI(MethodView):
#
#     @requires_auth(allowed_roles={'ADMIN': 'sempoadmin'})
#     def put(self, exchange_contract_id):
#
#         put_data = request.get_json()
#         token_id = put_data.get('token_id')
#
#         exchange_contract = ExchangeContract.query.get(exchange_contract_id)
#
#         if exchange_contract is None:
#             return make_response(jsonify(
#                 {'message': 'No Exchange Contract found for ID: {}'.format(exchange_contract_id)}))
#
#         token = Token.query.get(token_id)
#
#         if token is None:
#             return make_response(jsonify(
#                 {'message': 'No Token found for ID: {}'.format(token_id)}))
#
#         exchange_contract.exchangeable_tokens.append(token)
#
#         response_object = {
#             'message': 'success',
#         }
#
#         return make_response(jsonify(response_object)), 200
#
#
# exchange_blueprint.add_url_rule(
#     '/exchange_contract/<int:exchange_contract_id>/tokens',
#     view_func=ExchangeContractTokenAPI.as_view('token_view'),
#     methods=['PUT']
# )