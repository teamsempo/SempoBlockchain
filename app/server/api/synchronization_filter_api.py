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
        call = post_data.get('call', None)
        if not call:
            raise Exception('Please provide a \'call\' parameter')

        if call == 'add_transaction_filter':
            """
            Adds a new transaction filter for third party transaction sync
            contract_address - Address for contract
            contract_type - Type of contract to sync
            filter_parameters - Filter params to pass to webhook
            filter_type - Type of filter being used (E.g. TRANSFER, EXCHANGE)
            decimals - decimals used for currency (default: 18)
            block_epoch - Which block to use as zero-point in transaction sync. Use None to signifiy latest (Default: None)
            """
            contract_address = post_data.get('contract_address')
            contract_type = post_data.get('contract_type')
            filter_parameters = post_data.get('filter_parameters') 
            filter_type = post_data.get('filter_type')      
            decimals = post_data.get('decimals', 18)      
            block_epoch = post_data.get('block_epoch', None)      

            transaction_filter = add_transaction_filter(contract_address, contract_type, filter_parameters, filter_type, decimals = decimals, block_epoch = block_epoch)

            return make_response(jsonify(synchronization_filter_schema.dump(transaction_filter).data)), 201

        elif call == 'refetch_block_range':
            """
            Refetches a given range of blocks for third party transaction sync
            Params:
            filter_address - Address associated with a token.
            floor - Where to start fetching blocks
            ceiling - Where to finish fetching blocks
            """
            
            filter_address = post_data.get('filter_address')
            floor = int(post_data.get('floor'))
            ceiling = int(post_data.get('ceiling'))
            result = bt.force_fetch_block_range(filter_address, floor, ceiling)
            return make_response(jsonify({ 'status': result })), 201

        elif call == 'force_recall_webhook':
            """
            Forces a recall of the webhook for a given transaction
            Params:
            transaction_hash - Hash for the transaction you want to resync!
            """
            transaction_hash = post_data.get('transaction_hash')
            result = bt.force_recall_webhook(transaction_hash)
            return make_response(jsonify({ 'status': result })), 201

        else:
            raise Exception(f'{call} not a valid call')
            

class SynchronizationFilterMetricsAPI(MethodView):
    # Gets metrics regarding the status of third party sync
    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def get(self):
        """
        Gets status metrics for third party transaction sync
        Params:
        get_failed_block_fetches - 'true' or 'false', will return a list of blocks that failed being fetched (default false)
        get_failed_callbacks - 'true' or 'false', will return a list of callbacks which have failed (default false)
        """
        get_failed_block_fetches = request.args.get('get_failed_block_fetches', 'false').lower() in ['true', '1']
        get_failed_callbacks = request.args.get('get_failed_callbacks', 'false').lower() in ['true', '1']

        resp = {}
        if get_failed_block_fetches:
            resp['failed_block_fetches_by_contract'] = bt.get_failed_block_fetches()

        if get_failed_callbacks:
            resp['failed_callbacks_by_contract'] = bt.get_failed_callbacks()

        resp['metrics'] = bt.get_third_party_sync_metrics()
        return make_response(jsonify(resp)), 201

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

