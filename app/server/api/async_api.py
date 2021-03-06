from flask import Blueprint, g
from flask.views import MethodView
from server.utils.auth import requires_auth
from server.utils.executor import get_job_result
import json

async_blueprint = Blueprint('async', __name__)

class AsyncAPI(MethodView):
    @requires_auth
    def get(self, func_uuid):
        result = get_job_result(g.user.id, func_uuid)
        if result:
            return json.loads(result)
        else:
            return {'message': f'Async job with ID {func_uuid} for user {g.user.id} does not exist!'}


async_blueprint.add_url_rule(
    '/async/<func_uuid>/',
    view_func=AsyncAPI.as_view('async_view'),
    methods=['GET']
)
