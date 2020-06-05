from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView

from server import db, bt, red
from server.models.synchronization_filter import SynchronizationFilter
from server.models.synchronized_block import SynchronizedBlock
from server.utils.auth import requires_auth
from server.schemas import synchronization_filter_schema

import json

synchronization_filter_blueprint = Blueprint('synchronization_filter', __name__)


class SynchronizationFilterAPI(MethodView):

    #@requires_auth(allowed_basic_auth_types=('internal'))
    def post(self):
        test_filter = SynchronizationFilter(contract_address = '0x0fd6e8f2320c90e9d4b3a5bd888c4d556d20abd4', last_block_synchronized = 10265073)
        print(test_filter)
        test_block = SynchronizedBlock(block_number = 1)
        test_filter.blocks.append(test_block)
        test_filter.blocks.append(test_block)
        response_object = {"hi":"hello"}

        sync_filters = SynchronizationFilter.query.all()
        for f in sync_filters:
            db.session.delete(f)
        
        db.session.add(test_filter)

        # Build object with all filters, and store it in redis for the worker to consume
        cachable_sync_filters = []
        for filter in sync_filters:
            filter_cache_object = {
                'id': filter.id,
                'contract_address': filter.contract_address,
                'contract_type': filter.contract_type,
                'last_block_synchronized': filter.last_block_synchronized,
                'filter_parameters': filter.filter_parameters,
            }
            cachable_sync_filters.append(filter_cache_object)

        red.set('THIRD_PARTY_SYNC_FILTERS', json.dumps(cachable_sync_filters))

        # TODO: Make a function to request individaul transactions
        bt.force_third_party_transaction_sync()


        return make_response(jsonify(response_object)), 201

    def get(self):
        sync_filters = SynchronizationFilter.query.all()
        return make_response(jsonify(synchronization_filter_schema.dump(sync_filters).data)), 201

synchronization_filter_blueprint.add_url_rule(
    '/synchronization_filter/',
    view_func=SynchronizationFilterAPI.as_view('synchronization_filter_view'),
    methods=['POST', 'GET']
)
