from decimal import Decimal
import math

from sqlalchemy.orm import joinedload
from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView
from sqlalchemy import desc, asc

from server import db, red
from server.schemas import credit_transfers_schema, disbursement_schema, disbursements_schema
from server.models.disbursement import Disbursement
from server.models.transfer_account import TransferAccount
from server.models.credit_transfer import CreditTransfer
from server.utils.auth import requires_auth
from server.utils.transfer_filter import process_transfer_filters
from server.utils.search import generate_search_query
from server.utils.credit_transfer import make_payment_transfer, make_target_balance_transfer
from server.utils.transfer_enums import TransferSubTypeEnum, TransferModeEnum
from server.models.utils import paginate_query
from server.utils.executor import status_checkable_executor_job, add_after_request_checkable_executor_job
from server.utils.access_control import AccessControl

disbursement_blueprint = Blueprint('disbursement', __name__)


@status_checkable_executor_job
def make_transfers(disbursement_id, auto_resolve=False):
    send_transfer_account = g.user.default_organisation.queried_org_level_transfer_account
    from server.models.user import User
    from server.models.transfer_account import TransferAccount
    from server.models.disbursement import Disbursement
    disbursement = db.session.query(Disbursement).filter(Disbursement.id == disbursement_id).first()
    for idx, ta in enumerate(disbursement.transfer_accounts):
        user = ta.primary_user
        if disbursement.transfer_type == 'DISBURSEMENT':
            transfer = make_payment_transfer(
                disbursement.disbursement_amount,
                send_user=g.user,
                receive_user=db.session.query(User).filter(User.id == user.id).first(),
                send_transfer_account=send_transfer_account,
                receive_transfer_account=db.session.query(TransferAccount).filter(TransferAccount.id == ta.id).first(),
                transfer_subtype=TransferSubTypeEnum.DISBURSEMENT,
                transfer_mode=TransferModeEnum.WEB,
                automatically_resolve_complete=False,
            )
        if disbursement.transfer_type == 'RECLAMATION':
            transfer = make_payment_transfer(
                disbursement.disbursement_amount,
                send_user=db.session.query(User).filter(User.id == user.id).first(),
                send_transfer_account=db.session.query(TransferAccount).filter(TransferAccount.id == ta.id).first(),
                transfer_subtype=TransferSubTypeEnum.RECLAMATION,
                transfer_mode=TransferModeEnum.WEB,
                require_recipient_approved=False,
                automatically_resolve_complete=False,
            )
        if disbursement.transfer_type == 'BALANCE':
            transfer = make_target_balance_transfer(
                    disbursement.disbursement_amount,
                    db.session.query(User).filter(User.id == user.id).first(),
                    automatically_resolve_complete=False,
                    transfer_mode=TransferModeEnum.WEB,
                )

        disbursement.credit_transfers.append(transfer)
        if auto_resolve and disbursement.state == 'APPROVED':
            transfer.approvers = disbursement.approvers
            transfer.add_approver_and_resolve_as_completed()

        db.session.commit()
        percent_complete = ((idx + 1) / len(disbursement.transfer_accounts)) * 100
        yield {
            'message': 'success' if percent_complete == 100 else 'pending',
            'percent_complete': math.floor(percent_complete),
            'data': {'credit_transfers': credit_transfers_schema.dump(disbursement.credit_transfers).data}
        }

class MakeDisbursementAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def get(self):
        disbursements = db.session.query(Disbursement).order_by(Disbursement.id.desc()).all()

        response_object = {
            'status': 'success',
            'message': 'Successfully Loaded.',
            'data': {
                'disbursements': disbursements_schema.dump(disbursements).data
            }
        }
        return make_response(jsonify(response_object)), 200

    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def post(self):
        post_data = request.get_json()

        # --- Handle Parameters ---
        # HANDLE PARAM : label - Name for the disbursement
        label = post_data.get('label') or ''
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
        # HANDLE PARAM : transfer_type - Transfer type-- either DISBURSEMENT, RECLAMATION, or BALANCE
        transfer_type = post_data.get('transfer_type', 'DISBURSEMENT')
        if transfer_type not in ['DISBURSEMENT', 'RECLAMATION', 'BALANCE']:
            return { 'message': f'{transfer_type} not a valid transfer type. Please choose one of DISBURSEMENT, RECLAMATION, or BALANCE'}

        order_arg = request.args.get('order') or 'DESC'
        if order_arg.upper() not in ['ASC', 'DESC']:
            return { 'message': 'Invalid order value \'{}\'. Please use \'ASC\' or \'DESC\''.format(order_arg)}
        order = asc if order_arg.upper()=='ASC' else desc
        sort_by_arg = request.args.get('sort_by') or 'rank'

        # --- Build Disbursement Object ---
        d = Disbursement(
            creator_user = g.user,
            label = label,
            search_string = search_string,
            search_filter_params = encoded_filters,
            include_accounts = include_accounts,
            exclude_accounts = exclude_accounts,
            disbursement_amount = disbursement_amount,
            transfer_type = transfer_type
        )

        if include_accounts:
            transfer_accounts = db.session.query(TransferAccount).filter(TransferAccount.id.in_(include_accounts)).all()
        else:
            search_query = generate_search_query(search_string, filters, order, sort_by_arg, include_user=True)
            search_query = search_query.filter(TransferAccount.id.notin_(exclude_accounts))
            results = search_query.all()
            transfer_accounts = [r[0] for r in results] # Get TransferAccount (TransferAccount, searchRank, User)
        d.transfer_accounts.extend(transfer_accounts)

        db.session.flush()

        disbursement = disbursement_schema.dump(d).data

        response_object = {
            'data': {
                'status': 'success',
                'disbursement': disbursement
            }
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

        d = db.session.query(Disbursement).filter_by(id=disbursement_id).first()

        disbursement = disbursement_schema.dump(d).data

        response_object = {
            'status': 'success',
            'message': 'Successfully Loaded.',
            'items': total_items,
            'pages': total_pages,
            'last_fetched': new_last_fetched,
            'data': {
                'credit_transfers': transfer_list,
                'disbursement': disbursement
            }
        }
        return make_response(jsonify(response_object)), 200

    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def put(self, disbursement_id):
        put_data = request.get_json()
        action = put_data.get('action', '').upper()

        if not disbursement_id:
            return { 'message': 'Please provide a disbursement_id'}, 400
        if not action:
            return { 'message': 'Please provide an action'}, 400
        if action not in ['APPROVE', 'REJECT']: # We might want more actions later!
            return { 'message': f'{action} not a valid action' }, 400

        # Ensure it's impossible to have two threads operating on the same disbursement
        with red.lock(name=f'Disbursemnt{disbursement_id}', timeout=10, blocking_timeout=20):

            disbursement = Disbursement.query.filter(Disbursement.id == disbursement_id)\
                .options(joinedload(Disbursement.credit_transfers))\
                .first()

            if not disbursement:
                return { 'message': f'Disbursement with ID \'{disbursement_id}\' not found' }, 400

            if disbursement.state in ['APPROVED', 'REJECTED']:
                return { 'message': f'Disbursement with ID \'{disbursement_id}\' has already been set to {disbursement.state.lower()}!'}, 400

            if action == 'APPROVE':
                disbursement.approve()
                db.session.commit()
                auto_resolve = False
                if g.active_organisation.require_multiple_transfer_approvals or AccessControl.has_sufficient_tier(g.user.roles, 'ADMIN', 'superadmin'):
                    auto_resolve = True
                # A disbursement isn't necessarily approved after approve() is called, since we can require multiple approvers
                task_uuid = None
                if disbursement.state == 'APPROVED':
                    task_uuid = add_after_request_checkable_executor_job(
                        make_transfers, kwargs={'disbursement_id': disbursement.id, 'auto_resolve': auto_resolve}
                    )

                data = disbursement_schema.dump(disbursement).data
                return {
                    'status': 'success',
                    'data': {
                        'disbursement': data
                    },
                    'task_uuid': task_uuid
                }, 200

            if action == 'REJECT':
                disbursement.reject()
                db.session.commit()

                data = disbursement_schema.dump(disbursement).data

                return {
                    'status': 'success',
                    'data': {
                       'disbursement': data
                    },
                }, 200

disbursement_blueprint.add_url_rule(
    '/disbursement/',
    view_func=MakeDisbursementAPI.as_view('make_disbursement_view'),
    methods=['POST', 'GET']
)

disbursement_blueprint.add_url_rule(
    '/disbursement/<int:disbursement_id>/',
    view_func=DisbursementAPI.as_view('disbursement_view'),
    methods=['GET', 'PUT']
)
