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

        return make_response(jsonify(synchronization_filter_schema.dump(transaction_filter).data)), 201

class SynchronizationFilterMetricsAPI(MethodView):
    # Gets metrics regarding the status of third party sync
    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def get(self):
        get_failed_block_fetches = request.args.get('get_failed_block_fetches', 'false').lower() in ['true', '1']
        get_failed_callbacks = request.args.get('get_failed_callbacks', 'false').lower() in ['true', '1']

        resp = {}
        if get_failed_block_fetches:
            resp['failed_block_fetches_by_contract'] = bt.get_failed_block_fetches()

        if get_failed_callbacks:
            resp['failed_callbacks_by_contract'] = bt.get_failed_callbacks()

        resp['metrics'] = bt.get_third_party_sync_metrics()
        return make_response(jsonify(resp)), 201

class SynchronizationFilterRefetchAPI(MethodView):
    def post(self):
        filter_address = request.args.get('filter_address')
        floor = int(request.args.get('floor'))
        ceiling = int(request.args.get('ceiling'))
        result = bt.force_fetch_block_range(filter_address, floor, ceiling)
        return make_response(jsonify({ 'status': result })), 201

class SynchronizationFilterRecallWebhookAPI(MethodView):
    def post(self):
        transaction_hash = request.args.get('transaction_hash')
        bt.force_recall_webook(transaction_hash)
        

synchronization_filter_blueprint.add_url_rule(
    '/synchronization_filter/',
    view_func=SynchronizationFilterAPI.as_view('synchronization_filter_view'),
    methods=['POST']
)

synchronization_filter_blueprint.add_url_rule(
    '/synchronization_filter/status/',
    view_func=SynchronizationFilterMetricsAPI.as_view('synchronization_filter_metrics_view'),
    methods=['GET']
)

synchronization_filter_blueprint.add_url_rule(
    '/synchronization_filter/refetch_block_range/',
    view_func=SynchronizationFilterRefetchAPI.as_view('synchronization_filter_refetch_view'),
    methods=['POST']
)

synchronization_filter_blueprint.add_url_rule(
    '/synchronization_filter/recall_webhook/',
    view_func=SynchronizationFilterRecallWebhookAPI.as_view('synchronization_filter_recall_webhook_view'),
    methods=['POST']
)
