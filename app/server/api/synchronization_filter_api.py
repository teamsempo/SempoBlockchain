from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView

from server import db, bt, red
from server.utils.auth import requires_auth
from server.schemas import synchronization_filter_schema

import json

synchronization_filter_blueprint = Blueprint('synchronization_filter', __name__)


class SynchronizationFilterAPI(MethodView):

    @requires_auth(allowed_basic_auth_types=('internal'))
    def post(self):
        post_data = request.get_json()
        contract_address = post_data.get('contract_address')
        contract_type = post_data.get('contract_type')
        filter_type = post_data.get('filter_type')      
        filter_parameters = post_data.get('filter_parameters')      

        # TODO: Move this into a util and call it on app-start for each contract
        # Build object with all filters, and store it in redis for the worker to consume
        filter_cache_object = {
            'contract_address': contract_address,
            'contract_type': contract_type,
            'filter_parameters': filter_parameters,
            'filter_type': filter_type
        }

        bt.add_transaction_sync_filter(filter_cache_object)
        bt.force_third_party_transaction_sync()
        return make_response(jsonify(filter_cache_object)), 201

synchronization_filter_blueprint.add_url_rule(
    '/synchronization_filter/',
    view_func=SynchronizationFilterAPI.as_view('synchronization_filter_view'),
    methods=['POST']
)
