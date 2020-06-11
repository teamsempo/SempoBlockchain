from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView

from server import db, bt, red
from server.utils.auth import requires_auth
from server.schemas import synchronization_filter_schema

import json

synchronization_filter_blueprint = Blueprint('synchronization_filter', __name__)


class SynchronizationFilterAPI(MethodView):

    #@requires_auth(allowed_basic_auth_types=('internal'))
    def post(self):
        # TODO: Read this from POST data
        contract_address = '0x0fd6e8f2320c90e9d4b3a5bd888c4d556d20abd4'
        

        # Build object with all filters, and store it in redis for the worker to consume
        #cachable_sync_filters = []
        #for filter in sync_filters:
        filter_cache_object = {
            'contract_address': contract_address,
            'contract_type': 'ERC20',
            'filter_parameters': None,
            'filter_type': 'EXCHANGE'
        }
        #cachable_sync_filters.append(filter_cache_object)
        #filter_cache_objects = [filter_cache_object]
        #red.set('THIRD_PARTY_SYNC_FILTERS', json.dumps(cachable_sync_filters))

        bt.add_transaction_sync_filter(filter_cache_object)

        bt.force_third_party_transaction_sync()

        return make_response(jsonify(filter_cache_object)), 201

    def get(self):
        return True
        #sync_filters = SynchronizationFilter.query.all()
        #return make_response(jsonify(synchronization_filter_schema.dump(sync_filters).data)), 201

synchronization_filter_blueprint.add_url_rule(
    '/synchronization_filter/',
    view_func=SynchronizationFilterAPI.as_view('synchronization_filter_view'),
    methods=['POST', 'GET']
)
