from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView

from server import db
from server.utils.auth import requires_auth
from server.models.transfer_usage import TransferUsage
from server.models.user import User
from server.utils.mock_data import create_payments, create_disbursments, create_users


mock_data_blueprint = Blueprint('mock_Ddata', __name__)


class MockDataApi(MethodView):
    @requires_auth(allowed_basic_auth_types=('superadmin',))
    def post(self):
        post_data = request.get_json()

        number_of_users = post_data.get('number_of_users')
        number_of_transfers = post_data.get('number_of_transfers')
        number_of_days = post_data.get('number_of_days')
        amount_to_disburse = post_data.get('amount_to_disburse', 1000)

        safety_check = post_data.get('safety_check')
        total_users = User.query.execution_options(show_all=True).count()

        if safety_check != total_users:
            # Prevent a whole bunch of data being created unintentionally
            response_object = {
                'message': f"Failed Safety Check:"
                           f"Please set safety_check to the current number of users on the platform ({total_users})."
            }
            return make_response(jsonify(response_object)), 400

        transfer_usages = TransferUsage.query.all()
        admin_ta = g.active_organisation.org_level_transfer_account
        token = admin_ta.token

        total_disbursed = amount_to_disburse*number_of_users

        if admin_ta.balance < amount_to_disburse*number_of_users:
            response_object = {
                'message': f'Not enough balance to disburse. Have {admin_ta.balance}, need {total_disbursed}.'
            }

            return make_response(jsonify(response_object)), 400


        users_by_location = create_users(
            number_of_users,
            transfer_usages,
            g.active_organisation,
            created_offset=number_of_days
        )

        create_disbursments(users_by_location, g.user, token, amount_to_disburse, created_offset=number_of_days)
        create_payments(users_by_location, number_of_transfers, number_of_days, transfer_usages, token)

        response_object = {
            'message': 'success'
        }

        return make_response(jsonify(response_object)), 200


# add Rules for API Endpoints

mock_data_blueprint.add_url_rule(
    '/mock_data/',
    view_func=MockDataApi.as_view('mock_data_view'),
    methods=['POST']
)
