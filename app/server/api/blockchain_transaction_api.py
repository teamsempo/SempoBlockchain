from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView

from server import db, bt
from server.models.credit_transfer import CreditTransfer
from server.utils.auth import requires_auth
from server.models.credit_transfer import CreditTransfer
blockchain_transaction_blueprint = Blueprint('make_blockchain_transaction', __name__)

class BlockchainTransactionRPC(MethodView):

    @requires_auth
    def post(self):

        post_data = request.get_json()

        call = post_data.get('call')

        if call == 'RETRY_TASK':
            task_uuid = post_data.get('task_uuid')
            transfer = db.session.query(CreditTransfer)\
                .filter(CreditTransfer.blockchain_task_uuid == task_uuid)\
                .first()
            if transfer:
                transfer.send_blockchain_payload_to_worker()

            bt.retry_task(task_uuid)

            response_object = {
                'message': 'Starting Retry Task',
            }

            return make_response(jsonify(response_object)), 200

        if call == 'RETRY_FAILED_TASKS':

            min_task_id = post_data.get('min_task_id', None)
            max_task_id = post_data.get('max_task_id', None)
            retry_unstarted = post_data.get('retry_unstarted', False)

            res = bt.retry_failed(min_task_id, max_task_id, retry_unstarted)

            response_object = {
                'message': 'Retrying failed tasks',
                'data': res
            }

            return make_response(jsonify(response_object)), 200

        if call == 'DEDUPLICATE':
            min_task_id = post_data.get('min_task_id')
            max_task_id = post_data.get('max_task_id')

            res = bt.deduplicate(min_task_id, max_task_id)

            response_object = {
                'message': 'De-duplicating tasks',
                'data': res
            }

            return make_response(jsonify(response_object)), 200

        if call == 'REMOVE_PRIOR_TASK_DEPENDENCY':
            task_uuid = post_data.get('task_uuid')
            prior_task_uuid = post_data.get('prior_task_uuid')

            res = bt.remove_prior_task_dependency(task_uuid, prior_task_uuid)

            response_object = {
                'message': 'Removing Prior Task Dependency',
                'data': res
            }

            return make_response(jsonify(response_object)), 200

        if call == 'REMOVE_ALL_POSTERIOR_DEPENDENCIES':
            prior_task_uuid = post_data.get('prior_task_uuid')

            res = bt.remove_all_posterior_dependencies(prior_task_uuid)

            response_object = {
                'message': 'Removing All Posterior Dependencies',
                'data': res
            }

            return make_response(jsonify(response_object)), 200

        response_object = {
            'message': 'Call not recognised',
        }

        return make_response(jsonify(response_object)), 400


blockchain_transaction_blueprint.add_url_rule(
    '/blockchain_transaction_rpc/',
    view_func=BlockchainTransactionRPC.as_view('blockchain_transaction_rpc_view'),
    methods=['POST']
)

