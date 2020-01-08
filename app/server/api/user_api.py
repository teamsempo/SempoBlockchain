from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView

from server import db
from server.models.utils import paginate_query
from server.models.user import User
from server.models.transfer_account import TransferAccount
from server.schemas import user_schema, users_schema
from server.utils.auth import requires_auth
from server.utils.access_control import AccessControl
from server.utils import user as UserUtils


user_blueprint = Blueprint('user', __name__)


class UserAPI(MethodView):
    @requires_auth
    def get(self, user_id):

        can_see_full_details = AccessControl.has_suffient_role(
            g.user.roles, {'ADMIN': 'admin'})

        if not can_see_full_details:
            public_serial_number = request.args.get('public_serial_number')

            if public_serial_number:
                user = User.query.filter_by(
                    public_serial_number=public_serial_number.strip()).first()

                if user:
                    transfer_account = TransferAccount.query.get(
                        user.transfer_account_id)

                    if transfer_account:
                        response_object = {
                            'message': 'Successfully found transfer account!',
                            'data': {
                                'balance': transfer_account.balance
                            }
                        }

                        return make_response(jsonify(response_object)), 201

                    response_object = {
                        'message': 'No transfer_account for user: {}'.format(user),
                    }

                    return make_response(jsonify(response_object)), 400

                response_object = {
                    'message': 'No user for public serial number: {}'.format(public_serial_number),
                }

                return make_response(jsonify(response_object)), 400

            response_object = {
                'message': 'No public_serial_number provided',
            }

            return make_response(jsonify(response_object)), 400

        account_type_filter = request.args.get('account_type')
        if account_type_filter:
            account_type_filter = account_type_filter.lower()

        if user_id:
            user = User.query.get(user_id)
            #
            # user.cashout_authorised()

            if user is None:
                response_object = {
                    'message': 'No such user: {}'.format(user_id),
                }

                return make_response(jsonify(response_object)), 400

            response_object = {
                'status': 'success',
                'message': 'Successfully Loaded.',
                'data': {
                    'user': user_schema.dump(user).data
                }
            }

            return make_response(jsonify(response_object)), 201

        else:
            if account_type_filter == 'beneficiary':
                user_query = User.query.filter(User.has_beneficiary_role)

            elif account_type_filter == 'vendor':
                user_query = User.query.filter(User.has_vendor_role)

            elif account_type_filter == 'admin':
                user_query = User.query.filter(
                    User.has_admin_role).order_by(User.created.desc())

            else:
                user_query = User.query

            users, total_items, total_pages = paginate_query(user_query, User)

            if users is None:
                response_object = {
                    'message': 'No users',
                }

                return make_response(jsonify(response_object)), 400

            user_list = users_schema.dump(users).data

            response_object = {
                'message': 'Successfully Loaded.',
                'pages': total_pages,
                'items': total_items,
                'data': {
                    'users': user_list,
                }
            }
            return make_response(jsonify(response_object)), 201

    @requires_auth(allowed_roles={'ADMIN': 'subadmin'}, allowed_basic_auth_types=('external'))
    def post(self, user_id):

        post_data = request.get_json()
        organisation = g.active_organisation

        response_object, response_code = UserUtils.proccess_create_or_modify_user_request(
            post_data,
            organisation=organisation
        )

        if response_code == 200:
            db.session.commit()

        return make_response(jsonify(response_object)), response_code

    @requires_auth(allowed_roles={'ADMIN': 'subadmin'})
    def put(self, user_id):
        put_data = request.get_json()

        first_name = put_data.get('first_name')
        last_name = put_data.get('last_name')

        email = put_data.get('email')
        phone = put_data.get('phone')
        public_serial_number = put_data.get('public_serial_number')
        location = put_data.get('location')

        default_organisation_id = put_data.get('default_organisation_id')

        user = User.query.get(user_id)

        if not user:
            response_object = {
                'message': 'User not found'
            }
            return make_response(jsonify(response_object)), 400

        if first_name and not first_name == user.first_name:
            user.first_name = first_name

        if last_name and not last_name == user.last_name:
            user.last_name = last_name

        if email and not email == user.email:
            user.email = email

        if phone and not phone == user.phone:
            user.phone = phone

        if public_serial_number and not public_serial_number == user.public_serial_number:
            user.public_serial_number = public_serial_number

        if location and not location == user.location:
            user.location = location

        if default_organisation_id:
            user.default_organisation_id = default_organisation_id

        db.session.commit()

        response_object = {
            'status': 'success',
            'message': 'Successfully Edited User.',
            'data': {
                'user': user_schema.dump(user).data
            }
        }

        return make_response(jsonify(response_object)), 201


class ResetPinAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'sempoadmin'}, allowed_basic_auth_types=('external'))
    def post(self, user_id):

        post_data = request.get_json()
        reset_user_id = post_data.get('user_id')

        if reset_user_id is not None:
            user = User.query.get(reset_user_id)

            if user is None:
                return make_response(jsonify({'message': 'No user found for ID: {}'.format(reset_user_id)})), 404

            UserUtils.admin_reset_user_pin(user)

            response_object = {
                'status': 'success',
                'message': 'Successfully reset pin for user.',
                'data': {
                    'user': user_schema.dump(user).data
                }
            }
            return make_response(jsonify(response_object)), 200
        else:
            response_object = {
                'message': 'No user to reset pin for',
            }
            return make_response(jsonify(response_object)), 400


# add Rules for API Endpoints
user_blueprint.add_url_rule(
    '/user/',
    view_func=UserAPI.as_view('user_view'),
    methods=['GET', 'POST', 'PUT'],
    defaults={'user_id': None}
)

user_blueprint.add_url_rule(
    '/user/<int:user_id>/',
    view_func=UserAPI.as_view('single_user_view'),
    methods=['GET', 'PUT']
)

user_blueprint.add_url_rule(
    '/user/reset_pin/',
    view_func=ResetPinAPI.as_view('reset_pin'),
    methods=['POST'],
    defaults={'user_id': None}
)
