from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView

from server import db
from server.models.user import User
from server.utils.auth import requires_auth

geolocation_blueprint = Blueprint('geolocation', __name__)

class AddAddressLatLng(MethodView):

    @requires_auth(allowed_basic_auth_types=('internal',))
    def post(self):
        post_data = request.get_json()

        user_id = post_data['user_id']
        lat = post_data['lat']
        lng = post_data['lng']

        user = User.query.get(user_id)

        user.lat = lat
        user.lng = lng

        db.session.commit()

        response_object = {
            'status': 'success',
        }

        return make_response(jsonify(response_object)), 201

geolocation_blueprint.add_url_rule(
    '/geolocation/',
    view_func=AddAddressLatLng.as_view('add_address_latlng_view'),
    methods=['POST']
)
