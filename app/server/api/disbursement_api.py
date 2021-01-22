from decimal import Decimal

from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView
from sqlalchemy import desc, asc
from uuid import uuid4

from server import db
from server.schemas import credit_transfers_schema
from server.models.user import User
from server.models.disbursement import Disbursement
from server.models.transfer_account import TransferAccount
from server.models.credit_transfer import CreditTransfer
from server.utils.auth import requires_auth
from server.utils.transfer_filter import process_transfer_filters
from server.utils.search import generate_search_query
from server.utils.credit_transfer import make_payment_transfer
from server.utils.transfer_enums import TransferSubTypeEnum, TransferModeEnum
from server.models.utils import paginate_query, disbursement_credit_transfer_association_table
from sqlalchemy.orm import lazyload, joinedload

disbursement_blueprint = Blueprint('disbursement', __name__)

class MakeDisbursementAPI(MethodView):

    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def post(self):
        post_data = request.get_json()

        # --- Handle Parameters ---

        # HANDLE PARAM : search_stirng - Any search string. An empty string (or None) will just return everything!
        search_string = post_data.get('search_string') or ''
        # HANDLE PARAM : params - Standard filter object. Exact same as the ones Metrics uses!
        encoded_filters = post_data.get('params')
        filters = process_transfer_filters(encoded_filters)
        # HANDLE PARAM : include_accounts - Explicitly include these users
        include_accounts = post_data.get('include_accounts', [])
        # HANDLE PARAM : include_accounts - Explicitly exclude these users
        exclude_accounts = post_data.get('exclude_accounts', [])
        disbursement_amount = abs(round(Decimal(post_data.get('disbursement_amount') or 0),6))

        if include_accounts and exclude_accounts:
            return { 'message': 'Please either include or exclude users (include is additive from the whole search, while exclude is subtractive)'}

        order_arg = request.args.get('order') or 'DESC'
        if order_arg.upper() not in ['ASC', 'DESC']:
            return { 'message': 'Invalid order value \'{}\'. Please use \'ASC\' or \'DESC\''.format(order_arg)}
        order = asc if order_arg.upper()=='ASC' else desc
        sort_by_arg = request.args.get('sort_by') or 'rank'

        # --- Build Disbursement Object ---
        d = Disbursement()
        d.creator_user = g.user
        d.search_string = search_string
        d.search_filter_params = encoded_filters
        d.include_accounts = include_accounts
        d.exclude_accounts = exclude_accounts

        if include_accounts:
            transfer_accounts = db.session.query(TransferAccount).filter(TransferAccount.id.in_(include_accounts)).all()
            users = [ta.primary_user for ta in transfer_accounts]
        else:
            search_query = generate_search_query(search_string, filters, order, sort_by_arg, include_user=True)
            search_query = search_query.filter(TransferAccount.id.notin_(exclude_accounts))
            results = search_query.all()
            transfer_accounts = [r[0] for r in results] # Get TransferAccount (TransferAccount, searchRank, User)
            users = [r[2] for r in results] # Get User from (TransferAccount, searchRank, User)
        d.transfer_accounts.extend(transfer_accounts)
        db.session.add(d)

        send_transfer_account = g.user.default_organisation.queried_org_level_transfer_account
        for user, ta in zip(users, transfer_accounts):
            d.credit_transfers.append(make_payment_transfer(
                disbursement_amount,
                send_user=g.user,
                receive_user=user,
                send_transfer_account=send_transfer_account,
                receive_transfer_account=ta,
                transfer_subtype=TransferSubTypeEnum.DISBURSEMENT,
                transfer_mode=TransferModeEnum.WEB,
                automatically_resolve_complete=False,
            ))
        db.session.flush()
        response_object = {
            'status': 'success',
            'disbursement_id': d.id,
            'recipient_count': len(d.credit_transfers),
            'total_disbursement_amount': disbursement_amount*len(d.credit_transfers)
        }
        return make_response(jsonify(response_object)), 201


class DisbursementAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def get(self, disbursement_id):
        transfers = db.session.query(CreditTransfer)\
            .filter(CreditTransfer.disbursement.has(id=disbursement_id))\
            .options(joinedload(CreditTransfer.disbursement))

        transfers, total_items, total_pages, new_last_fetched = paginate_query(transfers)

        if transfers is None:
            response_object = {
                'message': 'No credit transfers',
            }

            return make_response(jsonify(response_object)), 400

        transfer_list = credit_transfers_schema.dump(transfers).data


        response_object = {
            'status': 'success',
            'message': 'Successfully Loaded.',
            'items': total_items,
            'pages': total_pages,
            'last_fetched': new_last_fetched,
            'data': {
                'credit_transfers': transfer_list,
            }
        }
        return make_response(jsonify(response_object)), 200

    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def post(self, disbursement_id):
        post_data = request.get_json()
        action = post_data.get('action', '').upper()

        if not disbursement_id:
            return { 'message': 'Please provide a disbursement_id'}
        if not action:
            return { 'message': 'Please provide an action'}
        if action not in ['EXECUTE']: # We might want more actions later!
            return { 'message': f'{action} not a valid action' }

        disbursement = Disbursement.query.filter(Disbursement.id == disbursement_id)\
            .options(joinedload(Disbursement.credit_transfers))\
            .first()

        if not disbursement:
            return { 'message': f'Disbursement with ID \'{disbursement_id}\' not found' }

        if disbursement.is_executed == True:
            return { 'message': f'Disbursement with ID \'{disbursement_id}\' has already been executed!' }

        batch_uuid = str(uuid4())
        for transfer in disbursement.credit_transfers:
            transfer.resolve_as_complete_and_trigger_blockchain(batch_uuid=batch_uuid)

        disbursement.is_executed = True
        return {
            'status': 'success',
        }

disbursement_blueprint.add_url_rule(
    '/disbursement/',
    view_func=MakeDisbursementAPI.as_view('make_disbursement_view'),
    methods=['POST']
)

disbursement_blueprint.add_url_rule(
    '/disbursement/<int:disbursement_id>/',
    view_func=DisbursementAPI.as_view('disbursement_view'),
    methods=['GET', 'POST']
)
