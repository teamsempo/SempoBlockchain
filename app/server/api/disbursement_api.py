from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView

from server import db
from server.models.user import User
from server.models.disbursement import Disbursement
from server.utils.auth import requires_auth
from server.utils.transfer_filter import process_transfer_filters

disbursement_blueprint = Blueprint('disbursement', __name__)

class DisbursementAPI(MethodView):

    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def post(self):
        post_data = request.get_json()

        # HANDLE PARAM : search_stirng - Any search string. An empty string (or None) will just return everything!
        search_string = post_data.get('search_string') or ''
        # HANDLE PARAM : params - Standard filter object. Exact same as the ones Metrics uses!
        encoded_filters = post_data.get('params')
        filters = process_transfer_filters(encoded_filters)
        # HANDLE PARAM : include_users - Explicitly include these users
        include_users = post_data.get('include_accounts')
        # HANDLE PARAM : include_users - Explicitly exclude these users
        exclude_users = post_data.get('exclude_accounts')

        d = Disbursement()
        d.creator_user = g.user
        d.search_string = search_string
        d.search_filter_params = encoded_filters
        d.include_users = include_users
        d.exclude_users = exclude_users
        from server.models.transfer_account import TransferAccount
        ta = db.session.query(TransferAccount).all()
        print(ta)
        
        d.transfer_accounts.extend(ta)
        db.session.add(d)
        db.session.commit()
        response_object = {
            'status': 'success',
        }

        return make_response(jsonify(response_object)), 201

disbursement_blueprint.add_url_rule(
    '/disbursement/',
    view_func=DisbursementAPI.as_view('disbursement_view'),
    methods=['POST']
)
