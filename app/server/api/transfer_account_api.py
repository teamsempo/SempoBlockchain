from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView
import datetime
import json
from sqlalchemy import func, asc, desc

from server import db
from server.models.utils import paginate_query
from server.models.transfer_account import TransferAccount, TransferAccountType
from server.schemas import transfer_accounts_schema, transfer_account_schema, \
    view_transfer_account_schema, view_transfer_accounts_schema
from server.utils.auth import requires_auth
from server.utils.access_control import AccessControl
from server.utils.transfer_filter import process_transfer_filters
from server.utils.search import generate_search_query

transfer_account_blueprint = Blueprint('transfer_account', __name__)


class TransferAccountAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'any'})
    def get(self, transfer_account_id):

        account_type_filter = request.args.get('account_type')
        result = None

        if transfer_account_id:
            transfer_account = TransferAccount.query.get(transfer_account_id)

            if transfer_account is None:
                response_object = {
                    'message': 'No such transfer account: {}'.format(transfer_account_id),
                }

                return make_response(jsonify(response_object)), 400

            if AccessControl.has_sufficient_tier(g.user.roles, 'ADMIN', 'admin'):
                result = transfer_account_schema.dump(transfer_account)
            elif AccessControl.has_any_tier(g.user.roles, 'ADMIN'):
                result = view_transfer_account_schema.dump(transfer_account)

            response_object = {
                'message': 'Successfully Loaded.',
                'data': {'transfer_account': result.data,}
            }
            return make_response(jsonify(response_object)), 201

        else:

            search_string = request.args.get('search_string') or ''
            # HANDLE PARAM : params - Standard filter object. Exact same as the ones Metrics uses!
            encoded_filters = request.args.get('params')
            filters = process_transfer_filters(encoded_filters)
            # HANDLE PARAM : order
            # Valid orders types are: `ASC` and `DESC`
            # Default: DESC
            order_arg = request.args.get('order') or 'DESC'
            if order_arg.upper() not in ['ASC', 'DESC']:
                return {'message': 'Invalid order value \'{}\'. Please use \'ASC\' or \'DESC\''.format(order_arg)}
            order = asc if order_arg.upper() == 'ASC' else desc
            # HANDLE PARAM: sort_by
            # Valid orders types are: first_name, last_name, email, date_account_created, rank, balance, status
            # Default: rank
            sort_by_arg = request.args.get('sort_by') or 'rank'

            base_query = generate_search_query(
                search_string, filters, order, sort_by_arg
            ).filter(TransferAccount.is_ghost != True)

            if account_type_filter == 'vendor':
                transfer_accounts_query = base_query.filter_by(is_vendor=True)
            elif account_type_filter == 'beneficiary':
                transfer_accounts_query = base_query.filter_by(is_beneficiary=True)
            else:
                pass
                # Filter Contract, Float and Organisation Transfer Accounts
                transfer_accounts_query = (base_query.filter(TransferAccount.account_type == TransferAccountType.USER))

            transfer_accounts, total_items, total_pages, new_last_fetched = paginate_query(transfer_accounts_query)

            if transfer_accounts is None:
                response_object = {
                    'message': 'No transfer accounts',
                }

                return make_response(jsonify(response_object)), 400

            if AccessControl.has_sufficient_tier(g.user.roles, 'ADMIN', 'admin'):
                result = transfer_accounts_schema.dump(transfer_accounts)
            elif AccessControl.has_any_tier(g.user.roles, 'ADMIN'):
                result = view_transfer_accounts_schema.dump(transfer_accounts)

            response_object = {
                'message': 'Successfully Loaded.',
                'items': total_items,
                'pages': total_pages,
                'last_fetched': new_last_fetched,
                'query_time': datetime.datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S"),
                'data': {'transfer_accounts': result.data}
            }
            return make_response(json.dumps(response_object), 200)

    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def put(self, transfer_account_id):
        put_data = request.get_json()

        transfer_account_id_list = put_data.get('transfer_account_id_list')
        approve = put_data.get('approve')

        transfer_account_name = put_data.get('transfer_account_name')
        
        notes = put_data.get('notes')

        payable_period_type = put_data.get('payable_period_type')
        payable_period_length = put_data.get('payable_period_length')
        payable_epoch = put_data.get('payable_epoch')

        if transfer_account_id:

            transfer_account = TransferAccount.query.get(transfer_account_id)

            if not transfer_account:
                response_object = {
                    'message': 'Transfer account not found'
                }
                return make_response(jsonify(response_object)), 400

            if transfer_account_name and not transfer_account_name == transfer_account.name:
                transfer_account.name = transfer_account_name

            if payable_period_type and not payable_period_type == transfer_account.payable_period_type:
                transfer_account.payable_period_type = payable_period_type

            if payable_period_length and not payable_period_length == transfer_account.payable_period_length:
                transfer_account.payable_period_length = payable_period_length

            if notes and not notes == transfer_account.notes:
                transfer_account.notes = notes

            if payable_epoch and not payable_epoch == transfer_account.payable_epoch:
                transfer_account.payable_epoch = payable_epoch

            if not approve == transfer_account.is_approved and transfer_account.is_approved is not True:
                transfer_account.is_approved = True
                transfer_account.approve_initial_disbursement()

            # Explicitly checking True and False since null is also possible
            if approve == True: 
                transfer_account.is_approved = True
            elif approve == False:
                transfer_account.is_approved = False

            db.session.flush()

            result = transfer_account_schema.dump(transfer_account)
            response_object = {
                'message': 'Successfully Edited Transfer Account.',
                'data': {
                    'transfer_account': result.data,
                }
            }
            return make_response(jsonify(response_object)), 201


        else:

            transfer_accounts = []
            response_list = []

            for transfer_account_id in transfer_account_id_list:

                transfer_account = TransferAccount.query.get(transfer_account_id)
                if not transfer_account:
                    response_list.append({
                        'status': 400,
                        'message': 'Transfer account id {} not found'.format(transfer_account_id)
                    })

                    continue
                if approve == True: 
                    transfer_account.is_approved = True
                elif approve == False:
                    transfer_account.is_approved = False

                if not transfer_account.is_approved and approve:
                    transfer_account.is_approved = True
                    transfer_account.approve_initial_disbursement()

                transfer_accounts.append(transfer_account)

            db.session.commit()

            response_object = {
                'status': 'success',
                'message': 'Successfully Edited Transfer Accounts.',
                'data': {
                    'transfer_accounts': transfer_accounts_schema.dump(transfer_accounts).data
                }
            }
            return make_response(jsonify(response_object)), 201

class BulkTransferAccountAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def put(self):
        put_data = request.get_json()
        # HANDLE PARAM : search_stirng - Any search string. An empty string (or None) will just return everything!
        search_string = put_data.get('search_string') or ''
        # HANDLE PARAM : params - Standard filter object. Exact same as the ones Metrics uses!
        encoded_filters = put_data.get('params')
        filters = process_transfer_filters(encoded_filters)
        # HANDLE PARAM : include_accounts - Explicitly include these users
        include_accounts = put_data.get('include_accounts', [])
        # HANDLE PARAM : include_accounts - Explicitly exclude these users
        exclude_accounts = put_data.get('exclude_accounts', [])

        approve = put_data.get('approve')

        if include_accounts and exclude_accounts:
            return { 'message': 'Please either include or exclude users (include is additive from the whole search, while exclude is subtractive)'}

        order_arg = request.args.get('order') or 'DESC'
        if order_arg.upper() not in ['ASC', 'DESC']:
            return { 'message': 'Invalid order value \'{}\'. Please use \'ASC\' or \'DESC\''.format(order_arg)}
        order = asc if order_arg.upper()=='ASC' else desc
        sort_by_arg = request.args.get('sort_by') or 'rank'

        if include_accounts:
            transfer_accounts = db.session.query(TransferAccount).filter(TransferAccount.id.in_(include_accounts)).all()
        else:
            search_query = generate_search_query(search_string, filters, order, sort_by_arg, include_user=True)
            search_query = search_query.filter(TransferAccount.id.notin_(exclude_accounts))
            results = search_query.all()
            transfer_accounts = [r[0] for r in results] # Get TransferAccount (TransferAccount, searchRank, User)

        for ta in transfer_accounts:
            if approve == True: 
                ta.is_approved = True
            elif approve == False:
                ta.is_approved = False

        db.session.commit()

        response_object = {
            'status': 'success',
            'message': 'Successfully Edited Transfer Accounts.',
        }
        return make_response(jsonify(response_object)), 201


# add Rules for API Endpoints
transfer_account_blueprint.add_url_rule(
    '/transfer_account/',
    view_func=TransferAccountAPI.as_view('transfer_account_view'),
    methods=['GET', 'PUT'],
    defaults={'transfer_account_id': None}
)

transfer_account_blueprint.add_url_rule(
    '/transfer_account/<int:transfer_account_id>/',
    view_func=TransferAccountAPI.as_view('single_transfer_account_view'),
    methods=['GET', 'PUT']
)

transfer_account_blueprint.add_url_rule(
    '/transfer_account/bulk/',
    view_func=BulkTransferAccountAPI.as_view('bulk_transfer_account_view'),
    methods=['PUT']
)