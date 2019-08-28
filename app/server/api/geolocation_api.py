from flask import Blueprint, request, make_response, jsonify, g, session
from flask.views import MethodView

from server import basic_auth, db, models
from server.models import CreditTransfer
from server.utils.auth import requires_auth

geolocation_blueprint = Blueprint('geolocation', __name__)

class AddAddressLatLng(MethodView):

    @requires_auth(allowed_basic_auth_types=('internal'))
    def post(self):
        post_data = request.get_json()

        user_id = post_data['user_id']
        lat = post_data['lat']
        lng = post_data['lng']

        user = models.User.query.get(user_id)

        user.lat = lat
        user.lng = lng

        db.session.commit()

        responseObject = {
            'status': 'success',
        }

        return make_response(jsonify(responseObject)), 201

geolocation_blueprint.add_url_rule(
    '/geolocation/',
    view_func=AddAddressLatLng.as_view('add_address_latlng_view'),
    methods=['POST']
)
