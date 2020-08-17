from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView

from server import db
from server.utils.auth import requires_auth
from server.models.credit_transfer import CreditTransfer
from server.models.exchange import Exchange

from server.models.worker_messages import WorkerMessages

from datetime import datetime
import time
blockchain_taskable_blueprint = Blueprint('blockchain_taskable', __name__)

class WorkerCallbackAPI(MethodView):
    @requires_auth(allowed_basic_auth_types=('internal',))
    def post(self):
        post_data = request.get_json()
        blockchain_task_uuid = post_data.get('blockchain_task_uuid')
        timestamp = datetime.fromtimestamp(post_data.get('timestamp'))
        blockchain_status = post_data.get('blockchain_status')
        error = post_data.get('error')
        message = post_data.get('message')
        blockchain_hash = post_data.get('hash')

        blockchain_tasks = []
        blockchain_tasks.extend(CreditTransfer.query.execution_options(show_all=True).filter_by(blockchain_task_uuid = blockchain_task_uuid).all())
        blockchain_tasks.extend(Exchange.query.execution_options(show_all=True).filter_by(blockchain_task_uuid = blockchain_task_uuid).all())

        if len(blockchain_tasks) == 0:
            return make_response(jsonify({
                'message': f'Blockchain Task with ID {blockchain_task_uuid} not found'
            })), 404

        for task in blockchain_tasks:
            # We're not guaranteed the worker's messages will arrive in order, so make sure we 
            # set the state as the latest
            if not task.last_worker_update or task.last_worker_update < timestamp:
                task.blockchain_status = blockchain_status
                task.last_worker_update = timestamp
                task.blockchain_hash = blockchain_hash
            if error or message:
                task.messages.append(WorkerMessages(error = error, message = message, worker_timestamp = timestamp))

        return ('', 204)


# add Rules for API Endpoints
blockchain_taskable_blueprint.add_url_rule(
    '/blockchain_taskable',
    view_func=WorkerCallbackAPI.as_view('blockchain_taskable_view'),
    methods=['POST']
)
