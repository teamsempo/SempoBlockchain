from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView

from server import db
from server.utils.auth import requires_auth
from server.utils import user as UserUtils
from server.utils.misc import AttributeDictProccessor
from server.constants import CREATE_USER_SETTINGS


worker_callback_blueprint = Blueprint('worker_callback', __name__)


class WorkerCallbackAPI(MethodView):
    @requires_auth(allowed_basic_auth_types=('external'))
    def post(self, user_id):

        return make_response(jsonify(response_object)), response_code


# add Rules for API Endpoints

worker_callback_blueprint.add_url_rule(
    '/worker_callback',
    view_func=WorkerCallbackAPI.as_view('worker_callback_view'),
    methods=['POST'],
    defaults={'user_id': None}
)
