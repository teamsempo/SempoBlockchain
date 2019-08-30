from flask import Blueprint, request, make_response, jsonify, g, session
from flask.views import MethodView

from server import db
from server.models import BlockchainAddress, User
from server.utils.auth import requires_auth
from server.schemas import blockchain_address_schema

blockchain_address_blueprint = Blueprint('blockchain_address', __name__)

class BlockchainAddressAPI(MethodView):

    @requires_auth
    def get(self):
        """
        :return: list of blockchain addresses
        """

        filter = request.args.get('filter','')

        if filter.lower() == 'vendor':
            users = User.query.filter_by(has_vendor_role=True).all()
            address_objects = [user.transfer_account.blockchain_address for user in users]

        elif filter.lower() == 'beneficiary':
            users = User.query.filter_by(has_beneficiary_role=True).all()
            address_objects = [user.transfer_account.blockchain_address for user in users]

        else:
            address_objects = BlockchainAddress.query.filter(BlockchainAddress.type == 'TRANSFER_ACCOUNT').all()

        responseObject = {
            'data': {
                'blockchain_addresses': blockchain_address_schema.dump(address_objects).data,
            }
        }

        return make_response(jsonify(responseObject)), 201


blockchain_address_blueprint.add_url_rule(
    '/blockchain_address/',
    view_func=BlockchainAddressAPI.as_view('blockchain_address'),
    methods=['GET']
)
