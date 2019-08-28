from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView
from server import db
from server.models import TransferUsage
from server.exceptions import IconNotSupportedException
from server.utils.auth import requires_auth

transfer_usage_blueprint = Blueprint('transfer_usage', __name__)


class TransferUsageAPI(MethodView):

    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def post(self):
        post_data = request.get_json()

        name = post_data.get('name')
        # MaterialCommunityIcons from https://oblador.github.io/react-native-vector-icons/
        icon = post_data.get('icon')
        priority = post_data.get('priority')
        # EG {'fr': 'fromage'}
        translations = post_data.get('translations')

        if name is None or icon is None:
            return make_response(jsonify({'message': 'Name and Icon must not be None'})), 400

        try:
            usage = TransferUsage(name=name, translations=translations, icon=icon, priority=priority)

        except IconNotSupportedException as e:
            return make_response(jsonify({'message': str(e)})), 400

        db.session.add(usage)
        db.session.commit()

        response_object = {
            'message': 'Created Transfer Usage'
        }

        return make_response(jsonify(response_object)), 201


transfer_usage_blueprint.add_url_rule(
    '/transfer_usage/',
    view_func=TransferUsageAPI.as_view('transfer_usage_view'),
    methods=['POST']
)
