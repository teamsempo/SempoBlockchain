from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView

from server import db
from server.models.ip_address import IpAddress
from server.utils.auth import requires_auth

ip_address_blueprint = Blueprint('ip_address', __name__)


class IpAddressLocationAPI(MethodView):

    @requires_auth(allowed_basic_auth_types=('internal'))
    def post(self):
        post_data = request.get_json()

        ip_address_id = post_data['ip_address_id']
        country = post_data['country']

        if ip_address_id is None:
            return make_response(jsonify({'message': 'Must provide IP Address ID'})), 400

        ip_address = IpAddress.query.get(ip_address_id)

        if ip_address is None:
            return make_response(jsonify({'message': 'Cannot find IP Address for ID: {}'.format(ip_address_id)})), 404

        ip_address.country = country

        db.session.commit()

        response_object = {
            'status': 'success',
        }

        return make_response(jsonify(response_object)), 201


ip_address_blueprint.add_url_rule(
    '/ip_address_location/',
    view_func=IpAddressLocationAPI.as_view('add_ip_address_location_view'),
    methods=['POST']
)
