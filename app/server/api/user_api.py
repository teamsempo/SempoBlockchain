from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView

from server import db
from server.models.utils import paginate_query
from server.models.user import User
from server.models.audit_history import AuditHistory
from server.schemas import user_schema, users_schema, audit_histories_schema
from server.utils.auth import requires_auth
from server.utils.access_control import AccessControl
from server.utils import user as UserUtils
from server.utils.auth import multi_org
from server.utils.attribute_preprocessor import standard_user_preprocess

from server.constants import CREATE_USER_SETTINGS

from server.exceptions import ResourceAlreadyDeletedError, TransferAccountDeletionError

user_blueprint = Blueprint('user', __name__)


class UserAPI(MethodView):
    @requires_auth
    @multi_org
    def get(self, user_id):

        can_see_full_details = AccessControl.has_suffient_role(
            g.user.roles, {'ADMIN': 'admin'})

        if not can_see_full_details:
            public_serial_number = request.args.get('public_serial_number')

            if public_serial_number:
                user = User.query.filter_by(
                    public_serial_number=public_serial_number.strip()).first()

                if user:

                    if user.default_transfer_account:
                        response_object = {
                            'message': 'Successfully found transfer account!',
                            'data': {
                                'balance': user.default_transfer_account.balance
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

            return make_response(jsonify(response_object)), 200

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

            users, total_items, total_pages, new_last_fetched = paginate_query(user_query)

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
                'last_fetched': new_last_fetched,
                'data': {
                    'users': user_list,
                }
            }
            return make_response(jsonify(response_object)), 200

    @requires_auth(allowed_roles={'ADMIN': 'subadmin'}, allowed_basic_auth_types=('external',), allow_query_string_auth=True)
    def post(self, user_id):
        """
        :arg preprocess: whether the data should be cleaned before attempting to create a user - for example converting
        keys such as "Phone" to "phone". Useful for third-party webhooks where we don't necessarily have a lot of
        control over how the user will specify fields.
        :arg allow_as_update: Whether to return an error when the user already exists for the supplied IDs,
        or instead update the existing user as a PUT request would.  Useful for third-party webhooks where
        PUT requests aren't supported.
        :arg: return_raw_on_error: whether to return the raw input data on an error - useful for diagnosing what a
        webhook actually tried to submit
        """

        raw_data = request.get_json()

        preprocess = request.args.get('preprocess', '').lower() == 'true'  #Defaults to false
        allow_as_update = request.args.get('allow_as_update', '').lower() == 'true' #Defaults to false
        return_raw_on_error = request.args.get('return_raw_on_error', '').lower() == 'true' #Defaults to false

        organisation = g.get('active_organisation')
        if organisation is None:
            return make_response(jsonify({'message': 'Organisation must be set'})), 400

        if preprocess:
            data = standard_user_preprocess(raw_data, CREATE_USER_SETTINGS)
        else:
            data = raw_data

        response_object, response_code = UserUtils.proccess_create_or_modify_user_request(
            data,
            organisation=organisation,
            allow_existing_user_modify=allow_as_update
        )

        if response_code == 200:
            db.session.commit()

        elif return_raw_on_error:
            response_object['raw_data'] = raw_data

        return make_response(jsonify(response_object)), response_code

    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def put(self, user_id):
        put_data = request.get_json()
        put_data['user_id'] = user_id

        response_object, response_code = UserUtils.proccess_create_or_modify_user_request(
            put_data,
            organisation=g.active_organisation,
            allow_existing_user_modify=True,
            modify_only=True
        )

        if response_code == 200:
            db.session.commit()

        return make_response(jsonify(response_object)), response_code

    @requires_auth(allowed_roles={'ADMIN': 'superadmin'})
    def delete(self, user_id):
        user = User.query.execution_options(show_deleted=True).get(user_id)

        if user is None:
            return make_response(jsonify({'message': 'No User Found for ID {}'.format(user_id)})), 404

        try:
            user.delete_user_and_transfer_account()
            response_object, status_code = {'message': 'User {} deleted'.format(user_id)}, 200
            db.session.commit()

        except (ResourceAlreadyDeletedError, TransferAccountDeletionError) as e:
            response_object, status_code = {'message': str(e)}, 400

        return make_response(jsonify(response_object)), status_code


class ResetPinAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'admin'}, allowed_basic_auth_types=('external',))
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

class AuditHistoryAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'any'}) # Do we want this to be just for superadmins?
    def get(self, user_id):
        history = db.session.query(AuditHistory).filter(AuditHistory.user_id == user_id).order_by(AuditHistory.created).all()

        response_object = {
            'status': 'success',
            'message': 'Successfully Loaded.',
            'data': {
                'changes': audit_histories_schema.dump(history).data
            }
        }

        return make_response(jsonify(response_object)), 201

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
    methods=['GET', 'PUT', 'DELETE']
)

user_blueprint.add_url_rule(
    '/user/reset_pin/',
    view_func=ResetPinAPI.as_view('reset_pin'),
    methods=['POST'],
    defaults={'user_id': None}
)

user_blueprint.add_url_rule(
    '/user/history/<int:user_id>/',
    view_func=AuditHistoryAPI.as_view('audit_user_history_view'),
    methods=['GET']
)
