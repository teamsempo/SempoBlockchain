from decimal import Decimal
import math
import datetime 

from sqlalchemy.orm import joinedload, load_only
from flask import Blueprint, request, make_response, jsonify, g, current_app
from flask.views import MethodView
from sqlalchemy import desc, asc

from server import db, red
from server.schemas import transfer_accounts_schema, disbursement_schema, disbursements_schema, credit_transfers_schema
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
from server.utils.metrics.metrics_cache import clear_metrics_cache, rebuild_metrics_cache

disbursement_blueprint = Blueprint('disbursement', __name__)

@status_checkable_executor_job
def make_transfers(disbursement_id, auto_resolve=False):
    yield {
        'message': 'Processing Bulk Disbursement',
        'percent_complete': 0,
    }

    send_transfer_account = g.user.default_organisation.queried_org_level_transfer_account
    from server.models.user import User
    from server.models.transfer_account import TransferAccount
    from server.models.disbursement import Disbursement
    disbursement = db.session.query(Disbursement).filter(Disbursement.id == disbursement_id)\
        .first()
    disbursement.mark_processing()
    db.session.commit()
    for idx, ta in enumerate(disbursement.transfer_accounts):
        try:
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
        except Exception as e:
            disbursement.errors = disbursement.errors + [str(ta) +': ' + str(e)]

        db.session.commit()
        percent_complete = ((idx + 1) / disbursement.recipient_count) * 100
        message = f'Creating transfer {idx+1} of {disbursement.recipient_count}'
        yield {
            'message': 'Success' if percent_complete == 100 else message,
            'percent_complete': math.floor(percent_complete),
        }
    disbursement.mark_complete()
    db.session.commit()
    clear_metrics_cache()
    rebuild_metrics_cache()

class MakeDisbursementAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def get(self):
        disbursements = db.session.query(Disbursement).order_by(Disbursement.id.desc())
        disbursements, total_items, total_pages, new_last_fetched = paginate_query(disbursements)
        response_object = {
            'message': 'Successfully Loaded.',
            'items': total_items,
            'pages': total_pages,
            'last_fetched': new_last_fetched,
            'query_time': datetime.datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S"),
            'data': {'disbursements': disbursements_schema.dump(disbursements).data}
        }
        return make_response(jsonify(response_object), 200)

    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def post(self):
        post_data = request.get_json()

        # --- Handle Parameters ---
        # HANDLE PARAM : label - Name for the disbursement
        label = post_data.get('label') or ''
        # HANDLE PARAM : search_string - Any search string. An empty string (or None) will just return everything!
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
            transfer_accounts = db.session.query(TransferAccount).filter(TransferAccount.id.in_(include_accounts)).options(load_only("id")).all()
        else:
            search_query = generate_search_query(search_string, filters, order, sort_by_arg, include_user=False)
            search_query = search_query.filter(TransferAccount.id.notin_(exclude_accounts))
            transfer_accounts = search_query.options(load_only("id")).all()
        d.transfer_accounts = transfer_accounts
        db.session.add(d)
        db.session.commit()
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
        d = db.session.query(Disbursement).filter_by(id=disbursement_id).first()
        credit_transfers, _, _, _ = paginate_query(d.credit_transfers)
        transfer_accounts, total_items, total_pages, last_fetched = paginate_query(d.transfer_accounts)
        disbursement = disbursement_schema.dump(d).data
        disbursement['credit_transfers'] = credit_transfers_schema.dump(credit_transfers)[0]
        disbursement['transfer_accounts'] = transfer_accounts_schema.dump(transfer_accounts)[0]
        response_object = {
            'status': 'success',
            'message': 'Successfully Loaded.',
            'items': total_items,
            'pages': total_pages,
            'last_fetched': last_fetched,
            'data': {
                'disbursement': disbursement
            }
        }
        return make_response(jsonify(response_object)), 200

    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def put(self, disbursement_id):
        put_data = request.get_json()
        action = put_data.get('action', '').upper()
        notes = put_data.get('notes') or ''

        if not disbursement_id:
            return { 'message': 'Please provide a disbursement_id'}, 400
        if not action:
            return { 'message': 'Please provide an action'}, 400
        if action not in ['APPROVE', 'REJECT']: # We might want more actions later!
            return { 'message': f'{action} not a valid action' }, 400

        # Ensure it's impossible to have two threads operating on the same disbursement
        with red.lock(name=f'Disbursemnt{disbursement_id}', timeout=10, blocking_timeout=20):

            disbursement = Disbursement.query.filter(Disbursement.id == disbursement_id)\
                .first()
            disbursement.notes = notes
            
            if not disbursement:
                return { 'message': f'Disbursement with ID \'{disbursement_id}\' not found' }, 400

            if disbursement.state in ['APPROVED', 'REJECTED']:
                return { 'message': f'Disbursement with ID \'{disbursement_id}\' has already been set to {disbursement.state.lower()}!'}, 400

            if action == 'APPROVE':
                # Checks if this can be afforded
                if disbursement.transfer_type == 'DISBURSEMENT':
                    org_balance = g.active_organisation.queried_org_level_transfer_account.balance
                    disbursement_amount = disbursement.total_disbursement_amount
                    if disbursement_amount > org_balance:
                        message = "Sender {} has insufficient balance. Has {}, needs {}.".format(
                            g.active_organisation.queried_org_level_transfer_account,
                            str(round(org_balance / 100, 2)),
                            str(round(disbursement_amount / 100, 2))
                        )
                        response_object = {'message': str(message)}
                        return make_response(jsonify(response_object)), 400
                disbursement.approve()
                db.session.commit()
                auto_resolve = False
                if current_app.config['REQUIRE_MULTIPLE_APPROVALS'] or AccessControl.has_sufficient_tier(g.user.roles, 'ADMIN', 'superadmin'):
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
