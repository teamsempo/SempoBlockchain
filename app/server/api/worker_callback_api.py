from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView

from server import db
from server.utils.auth import requires_auth
from server.models.credit_transfer import CreditTransfer
from server.models.worker_messages import WorkerMessages

from datetime import datetime
import time
worker_callback_blueprint = Blueprint('worker_callback', __name__)

class WorkerCallbackAPI(MethodView):
    @requires_auth(allowed_basic_auth_types=('internal'))
    def post(self):
        post_data = request.get_json()
        blockchain_task_uuid = post_data.get('blockchain_task_uuid')
        timestamp = datetime.fromtimestamp(post_data.get('timestamp'))
        blockchain_status = post_data.get('blockchain_status')
        error = post_data.get('error')
        message = post_data.get('message')
        blockchain_hash = post_data.get('hash')

        transfer = CreditTransfer.query.execution_options(show_all=True).filter_by(blockchain_task_uuid = blockchain_task_uuid).first()
        if not transfer:
            # Single 2s sleep/retry on failure. Sometimtes when running locally the CreditTransfer object will not be committed yet
            # by the time the worker hits the callback
            time.sleep(2)
            transfer = CreditTransfer.query.execution_options(show_all=True).filter_by(blockchain_task_uuid = blockchain_task_uuid).first()

        if not transfer:
            return ('Credit transfer with ID {blockchain_task_uuid} not found', 404)
        # We're not guaranteed the worker's messages will arrive in order, so make sure we 
        # set the state as the latest
        if not transfer.last_worker_update or transfer.last_worker_update < timestamp:
            transfer.blockchain_status = blockchain_status
            transfer.last_worker_update = timestamp
            transfer.blockchain_hash = blockchain_hash
        if error or message:
            transfer.messages.append(WorkerMessages(error = error, message = message))
        return ('', 204)


# add Rules for API Endpoints
worker_callback_blueprint.add_url_rule(
    '/worker_callback',
    view_func=WorkerCallbackAPI.as_view('worker_callback_view'),
    methods=['POST']
)
