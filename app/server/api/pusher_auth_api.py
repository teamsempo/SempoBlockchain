import datetime
from flask import Blueprint, request, make_response, jsonify, g, current_app
from flask.views import MethodView

from server import pusher_client
from server.utils.auth import requires_auth, AccessControl

pusher_auth_blueprint = Blueprint('pusher_auth', __name__)


class PusherAuthAPI(MethodView):

    @requires_auth
    def post(self):

        channel = request.form['channel_name']

        if (channel == 'private-user-{}-{}'.format(current_app.config['DEPLOYMENT_NAME'], g.user.id)
            or (AccessControl.has_suffient_role(g.user.roles,{'ADMIN': 'admin'})
                and channel == current_app.config['PUSHER_ENV_CHANNEL'])):

            auth = pusher_client.authenticate(
                channel=channel,
                socket_id=request.form['socket_id']
            )

            return make_response(jsonify(auth)), 200
        else:
            response_object = {
                'message': 'channel {} not authorised'.format(channel)
            }
            return make_response(jsonify(response_object)), 401

class PusherSuperAdminAuthAPI(MethodView):

    @requires_auth(allowed_roles={'ADMIN': 'superadmin'})
    def post(self):
        auth = pusher_client.authenticate(
            channel=request.form['channel_name'],
            socket_id=request.form['socket_id']
        )

        return make_response(jsonify(auth)), 200



pusher_auth_blueprint.add_url_rule(
    '/pusher/auth',
    view_func=PusherAuthAPI.as_view('pusher_auth_view'),
    methods=['POST']
)

pusher_auth_blueprint.add_url_rule(
    '/pusher/superauth',
    view_func=PusherSuperAdminAuthAPI.as_view('pusher_superauth_view'),
    methods=['POST']
)
