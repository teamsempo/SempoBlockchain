from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView

from server import db
from server.utils.auth import requires_auth
from server.utils import user as UserUtils
from server.utils.misc import AttributeDictProccessor
from server.constants import CREATE_USER_SETTINGS


worker_callback_blueprint = Blueprint('worker_callback', __name__)

class WorkerCallbackAPI(MethodView):
    @requires_auth(allowed_basic_auth_types=('internal'))
    def post(self):
        post_data = request.get_json()
        blockchain_task_uuid = post_data.get('blockchain_task_uuid')
        timestamp = post_data.get('timestamp')
        blockchain_task_uuid = post_data.get('timestamp')
        blockchain_status = post_data.get('blockchain_status')
        error = post_data.get('error')
        message = post_data.get('message')
        
        hash = post_data.get('hash')
        print(post_data)
        print(blockchain_task_uuid)
        print(timestamp)
        print(blockchain_task_uuid)
        print(blockchain_status)
        print(error)
        print(message)
        print(hash)

        return ('', 204)


# add Rules for API Endpoints

worker_callback_blueprint.add_url_rule(
    '/worker_callback',
    view_func=WorkerCallbackAPI.as_view('worker_callback_view'),
    methods=['POST']
)
