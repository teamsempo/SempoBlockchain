from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView

from server import db
from server.models.synchronization_filter import SynchronizationFilter
from server.models.synchronized_block import SynchronizedBlock
from server.utils.auth import requires_auth
from server.schemas import synchronization_filter_schema


synchronization_filter_blueprint = Blueprint('synchronization_filter', __name__)


class SynchronizationFilterAPI(MethodView):

    #@requires_auth(allowed_basic_auth_types=('internal'))
    def post(self):
        test_filter = SynchronizationFilter(contract_address = 0, last_block_synchronized = 0)
        print(test_filter)
        test_block = SynchronizedBlock(block_number = 1)
        test_filter.blocks.append(test_block)
        test_filter.blocks.append(test_block)
        response_object = {"hi":"hello"}
        print(test_filter.blocks)
        db.session.add(test_filter)
        return make_response(jsonify(response_object)), 201

    def get(self):
        sync_filters = SynchronizationFilter.query.all()
        return make_response(jsonify(synchronization_filter_schema.dump(sync_filters).data)), 201

synchronization_filter_blueprint.add_url_rule(
    '/synchronization_filter/',
    view_func=SynchronizationFilterAPI.as_view('synchronization_filter_view'),
    methods=['POST', 'GET']
)
