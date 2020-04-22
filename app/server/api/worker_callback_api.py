from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView

from server import db
from server.utils.auth import requires_auth
from server.models.credit_transfer import CreditTransfer

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
        
        hash = post_data.get('hash')
        print(post_data)
        print(blockchain_task_uuid)
        print(timestamp)
        print(blockchain_status)
        print(error)
        print(message)
        print(hash)

        # lookup blockchain_task_uuid
        print('===+++++++++++++++')
        print(post_data)
        print('\''+blockchain_task_uuid+'\'')
        time.sleep(2)
        transfer = CreditTransfer.query.execution_options(show_all=True).filter_by(blockchain_task_uuid = blockchain_task_uuid).first()
       # 
#
        print(transfer)
        print("++++222+")
#
       # print(transfer.last_worker_update)
       # print("+++++")
       # if not transfer.last_worker_update:
       #     print('AAaaa')
       # 

        if not transfer.last_worker_update or transfer.last_worker_update < timestamp:
            print('saving')
            print(blockchain_status)
            transfer.blockchain_status = blockchain_status
            transfer.last_worker_update = timestamp
       # print('0-')
        return ('', 204)


# add Rules for API Endpoints

worker_callback_blueprint.add_url_rule(
    '/worker_callback',
    view_func=WorkerCallbackAPI.as_view('worker_callback_view'),
    methods=['POST']
)
