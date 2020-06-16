from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView
import json

from server import bt
from server.utils.auth import requires_auth
from server.utils.synchronization_filter import add_transaction_filter
from server.schemas import synchronization_filter_schema

synchronization_filter_blueprint = Blueprint('synchronization_filter', __name__)

class SynchronizationFilterAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def post(self):
        post_data = request.get_json()
        contract_address = post_data.get('contract_address')
        contract_type = post_data.get('contract_type')
        filter_parameters = post_data.get('filter_parameters') 
        filter_type = post_data.get('filter_type')      
        decimals = post_data.get('decimals', 18)      
        block_epoch = post_data.get('block_epoch', None)      

        transaction_filter = add_transaction_filter(contract_address, contract_type, filter_parameters, filter_type, decimals = decimals, block_epoch = block_epoch)
        #bt.force_third_party_transaction_sync()
        return make_response(jsonify(synchronization_filter_schema.dump(transaction_filter).data)), 201

synchronization_filter_blueprint.add_url_rule(
    '/synchronization_filter/',
    view_func=SynchronizationFilterAPI.as_view('synchronization_filter_view'),
    methods=['POST']
)
