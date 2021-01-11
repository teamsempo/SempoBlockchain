from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView
from sqlalchemy import or_, not_
import json
from decimal import Decimal
from uuid import uuid4
from server import db
from server.models.token import Token
from server.models.utils import paginate_query
from server.models.credit_transfer import CreditTransfer
from server.models.blockchain_address import BlockchainAddress
from server.models.transfer_account import TransferAccount, TransferAccountType

from server.schemas import credit_transfers_schema, credit_transfer_schema, view_credit_transfers_schema
from server.utils.auth import requires_auth
from server.utils.access_control import AccessControl
from server.utils.credit_transfer import find_user_with_transfer_account_from_identifiers
from server.utils.transfer_enums import TransferTypeEnum, TransferSubTypeEnum, TransferModeEnum, TransferStatusEnum
from server.utils.credit_transfer import (
    make_payment_transfer,
    make_target_balance_transfer,
    make_blockchain_transfer)

from server.utils.user import create_transfer_account_if_required
from server.utils.auth import multi_org

from server.exceptions import NoTransferAccountError, UserNotFoundError, InsufficientBalanceError, AccountNotApprovedError, \
    InvalidTargetBalanceError, BlockchainError

credit_transfer_blueprint = Blueprint('credit_transfer', __name__)


class CreditTransferAPI(MethodView):
    @multi_org
    @requires_auth(allowed_roles={'ADMIN': 'any'})
    def get(self, credit_transfer_id):
        transfer_account_ids = request.args.get('transfer_account_ids')
        transfer_type = request.args.get('transfer_type', 'ALL')
        transfer_list = None
        if transfer_type:
            transfer_type = transfer_type.upper()

        if credit_transfer_id:

            credit_transfer = CreditTransfer.query.get(credit_transfer_id)

            if credit_transfer is None:
                return make_response(jsonify({'message': 'Credit transfer not found'})), 404

            if AccessControl.has_sufficient_tier(g.user.roles, 'ADMIN', 'admin'):
                transfer_list = credit_transfers_schema.dump([credit_transfer]).data
            elif AccessControl.has_any_tier(g.user.roles, 'ADMIN'):
                transfer_list = view_credit_transfers_schema.dump([credit_transfer]).data

            transfer_stats = []

            response_object = {
                'status': 'success',
                'message': 'Successfully Loaded.',
                'data': {
                    'credit_transfer': transfer_list,
                    'transfer_stats': transfer_stats
                }
            }

            return make_response(jsonify(response_object)), 200

        else:

            query = CreditTransfer.query
            transfer_list = None

            if transfer_type != 'ALL':
                try:
                    transfer_type_enum = TransferTypeEnum[transfer_type]
                    query = query.filter(CreditTransfer.transfer_type == transfer_type_enum)
                except KeyError:
                    response_object = {
                        'message': 'Invalid Filter: Transfer Type ',
                    }
                    return make_response(jsonify(response_object)), 400

            if transfer_account_ids:
                # We're getting a list of transfer accounts - parse
                try:
                    parsed_transfer_account_ids = list(
                        map(lambda x: int(x), filter(None, transfer_account_ids.split(','))))

                except ValueError:
                    response_object = {
                        'message': 'Invalid Filter: Transfer Account IDs ',
                    }
                    return make_response(jsonify(response_object)), 400

                if parsed_transfer_account_ids:

                    query = query.filter(
                        or_(CreditTransfer.recipient_transfer_account_id.in_(parsed_transfer_account_ids),
                            CreditTransfer.sender_transfer_account_id.in_(parsed_transfer_account_ids)))

            transfers, total_items, total_pages, new_last_fetched = paginate_query(query)

            if AccessControl.has_sufficient_tier(g.user.roles, 'ADMIN', 'admin'):
                transfer_list = credit_transfers_schema.dump(transfers).data
            elif AccessControl.has_sufficient_tier(g.user.roles, 'ADMIN', 'view'):
                transfer_list = view_credit_transfers_schema.dump(transfers).data

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

    @requires_auth(allowed_roles={'ADMIN': 'superadmin'})
    def put(self, credit_transfer_id):

        put_data = request.get_json()

        action = put_data.get('action', '').upper()

        credit_transfer = CreditTransfer.query.get(credit_transfer_id)

        if credit_transfer is None:
            response_object = {
                'message': 'Credit transfer not found for id {}'.format(credit_transfer_id),
            }
            return make_response(jsonify(response_object)), 404

        if credit_transfer.transfer_status.value != 'PENDING':
            response_object = {
                'message': 'Transfer status is {}. Must be PENDING to modify'
                    .format(credit_transfer.transfer_status.value)
            }
            return make_response(jsonify(response_object)), 400

        ALLOWED_ACTIONS = ['COMPLETE', 'REJECT']
        if action not in ALLOWED_ACTIONS:
            response_object = {
                'message': 'Action is {} not one of {}'.format(action, ALLOWED_ACTIONS)
            }
            return make_response(jsonify(response_object)), 400

        try:
            if action == 'COMPLETE':
                credit_transfer.resolve_as_complete_and_trigger_blockchain()

            elif action == 'REJECT':
                credit_transfer.resolve_as_rejected()

        except Exception as e:

            db.session.commit()

            response_object = {
                'message': str(e),
            }
            return make_response(jsonify(response_object)), 400

        db.session.flush()

        response_object = {
            'message': 'Modification successful',
            'data': {
                'credit_transfer': credit_transfer_schema.dump(credit_transfer).data,
            }
        }

        return make_response(jsonify(response_object)), 201

    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def post(self, credit_transfer_id):

        auto_resolve = AccessControl.has_sufficient_tier(g.user.roles, 'ADMIN', 'superadmin')

        post_data = request.get_json()

        uuid = post_data.get('uuid')

        queue = 'low-priority'

        transfer_type = post_data.get('transfer_type')
        transfer_amount = abs(round(Decimal(post_data.get('transfer_amount') or 0),6))
        token_id = post_data.get('token_id')
        target_balance = post_data.get('target_balance')

        transfer_use = post_data.get('transfer_use')
        try:
            use_ids = transfer_use.split(',')  # passed as '3,4' etc.
        except AttributeError:
            use_ids = transfer_use

        sender_user_id = post_data.get('sender_user_id')
        recipient_user_id = post_data.get('recipient_user_id')

        # These could be phone numbers, email, nfc serial numbers, card numbers etc
        sender_public_identifier = post_data.get('sender_public_identifier')
        recipient_public_identifier = post_data.get('recipient_public_identifier')

        sender_transfer_account_id = post_data.get('sender_transfer_account_id')
        recipient_transfer_account_id = post_data.get('recipient_transfer_account_id')

        recipient_transfer_accounts_ids = post_data.get('recipient_transfer_accounts_ids')
        
        # invert_recipient_list will send to everyone _except_ for the users in recipient_transfer_accounts_ids 
        invert_recipient_list = post_data.get('invert_recipient_list', False)
        invert_recipient_list = False if invert_recipient_list == False else True

        credit_transfers = []
        response_list = []
        is_bulk = False
        transfer_card = None

        if uuid:
            existing_transfer = CreditTransfer.query.filter_by(uuid = uuid).first()

            # We return a 201 here so that the client removes the uuid from the cache
            response_object = {
                'message': 'Transfer Successful',
                'data': {
                    'credit_transfer': credit_transfer_schema.dump(existing_transfer).data,
                }
            }
            return make_response(jsonify(response_object)), 201


        if transfer_amount <= 0 and not target_balance:
            response_object = {
                'message': 'Transfer amount must be positive',
            }
            return make_response(jsonify(response_object)), 400

        if recipient_transfer_accounts_ids:
            is_bulk = True
            batch_uuid = str(uuid4())


            if transfer_type not in ["DISBURSEMENT", "BALANCE"]:
                response_object = {
                    'message': 'Bulk transfer must be either disbursement or balance',
                }
                return make_response(jsonify(response_object)), 400

            transfer_user_list = []
            individual_sender_user = None

            if invert_recipient_list:
                all_accounts_query = TransferAccount.query.filter(TransferAccount.is_ghost != True).filter_by(organisation_id=g.active_organisation.id)
                all_user_accounts_query = (all_accounts_query.filter(TransferAccount.account_type == TransferAccountType.USER))
                all_accounts_except_selected_query = all_user_accounts_query.filter(not_(TransferAccount.id.in_(recipient_transfer_accounts_ids)))
                for individual_recipient_user in all_accounts_except_selected_query.all():
                    transfer_user_list.append((individual_sender_user, individual_recipient_user.primary_user, None))
            else:
                for transfer_account_id in recipient_transfer_accounts_ids:
                    try:
                        individual_recipient_user, transfer_card = find_user_with_transfer_account_from_identifiers(
                            None, None, transfer_account_id)
                        transfer_user_list.append((individual_sender_user, individual_recipient_user, transfer_card))
                    except (NoTransferAccountError, UserNotFoundError) as e:
                        response_list.append({'status': 400, 'message': str(e)})

        else:
            batch_uuid = None
            try:
                individual_sender_user, transfer_card = find_user_with_transfer_account_from_identifiers(
                    sender_user_id,
                    sender_public_identifier,
                    sender_transfer_account_id)

                individual_recipient_user, _ = find_user_with_transfer_account_from_identifiers(
                    recipient_user_id,
                    recipient_public_identifier,
                    recipient_transfer_account_id)
                transfer_user_list = [(individual_sender_user, individual_recipient_user, transfer_card)]

            except Exception as e:
                response_object = {
                    'message': str(e),
                }
                return make_response(jsonify(response_object)), 400

        if token_id:
            token = Token.query.get(token_id)
            if not token:
                response_object = {
                    'message': 'Token not found'
                }
                return make_response(jsonify(response_object)), 404
        else:
            active_organisation = g.active_organisation
            if active_organisation is None:
                response_object = {
                    'message': 'Must provide token_id'
                }
                return make_response(jsonify(response_object)), 400
            else:
                token = active_organisation.token


        for sender_user, recipient_user, transfer_card in transfer_user_list:
            try:
                if transfer_type == 'PAYMENT':
                    transfer = make_payment_transfer(
                        transfer_amount,
                        token=token,
                        send_user=sender_user,
                        receive_user=recipient_user,
                        transfer_use=transfer_use,
                        transfer_mode=TransferModeEnum.WEB,
                        uuid=uuid,
                        automatically_resolve_complete=auto_resolve,
                        queue=queue,
                        batch_uuid=batch_uuid,
                        transfer_card=transfer_card
                    )

                elif transfer_type == 'RECLAMATION':
                    transfer = make_payment_transfer(
                        transfer_amount,
                        token=token,
                        send_user=sender_user,
                        uuid=uuid,
                        transfer_subtype=TransferSubTypeEnum.RECLAMATION,
                        transfer_mode=TransferModeEnum.WEB,
                        require_recipient_approved=False,
                        automatically_resolve_complete=auto_resolve,
                        queue=queue,
                        batch_uuid=batch_uuid
                    )

                elif transfer_type == 'DISBURSEMENT':
                    transfer = make_payment_transfer(
                        transfer_amount,
                        token=token,
                        send_user=g.user,
                        receive_user=recipient_user,
                        uuid=uuid,
                        transfer_subtype=TransferSubTypeEnum.DISBURSEMENT,
                        transfer_mode=TransferModeEnum.WEB,
                        automatically_resolve_complete=auto_resolve,
                        queue=queue,
                        batch_uuid=batch_uuid
                    )

                elif transfer_type == 'BALANCE':
                    transfer = make_target_balance_transfer(
                        target_balance,
                        recipient_user,
                        uuid=uuid,
                        automatically_resolve_complete=auto_resolve,
                        transfer_mode=TransferModeEnum.WEB,
                        queue=queue,
                    )

            except (InsufficientBalanceError,
                    AccountNotApprovedError,
                    InvalidTargetBalanceError,
                    BlockchainError,
                    Exception) as e:

                if is_bulk:
                    response_list.append({'status': 400, 'message': str(e)})

                else:
                    db.session.commit()
                    response_object = {'message': str(e)}
                    return make_response(jsonify(response_object)), 400

            else:
                message = 'Transfer Successful' if auto_resolve else 'Transfer Pending. Must be approved.'
                if is_bulk:
                    credit_transfers.append(transfer)
                    response_list.append({'status': 201, 'message': message})

                else:
                    db.session.flush()
                    credit_transfer = credit_transfer_schema.dump(transfer).data

                    response_object = {
                        'message': message,
                        'is_create': True,
                        'data': {
                            'credit_transfer': credit_transfer,
                        }
                    }

                    return make_response(jsonify(response_object)), 201

        db.session.flush()

        message = 'Bulk Transfer Creation Successful' if auto_resolve else 'Bulk Transfer Pending. Must be approved.'
        response_object = {
            'message': message,
            'bulk_responses': response_list,
            'data': {
                'credit_transfers': credit_transfers_schema.dump(credit_transfers).data
            }
        }

        return make_response(jsonify(response_object)), 201


class ConfirmWithdrawalAPI(MethodView):

    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def post(self):

        post_data = request.get_json()

        withdrawal_id_list = post_data.get('withdrawal_id_list')
        credit_transfers = []

        for withdrawal_id_string in withdrawal_id_list:

            withdrawal_id = int(withdrawal_id_string)

            withdrawal = CreditTransfer.query.get(withdrawal_id)

            withdrawal.resolve_as_complete_and_trigger_blockchain()

            credit_transfers.append(CreditTransfer.query.get(withdrawal_id_string))

        db.session.flush()

        response_object = {
            'message': 'Withdrawal Confirmed',
            'data': {
                'credit_transfers': credit_transfers_schema.dump(credit_transfers).data,
            }
        }

        return make_response(jsonify(response_object)), 201


class InternalCreditTransferAPI(MethodView):
    @requires_auth(allowed_basic_auth_types=('internal',))
    def post(self):
        post_data = request.get_json()

        transfer_amount = post_data.get('transfer_amount')
        sender_blockchain_address = post_data.get('sender_blockchain_address')
        recipient_blockchain_address = post_data.get('recipient_blockchain_address')
        blockchain_transaction_hash = post_data.get('blockchain_transaction_hash')
        contract_address = post_data.get('contract_address')

        transfer = CreditTransfer.query.execution_options(show_all=True).filter_by(blockchain_hash=blockchain_transaction_hash).first()
        # Case 1: Transfer exists in the database already. Just fetech it and return it in that case
        if transfer:
            credit_transfer = credit_transfer_schema.dump(transfer).data
            response_object = {
                'message': 'Transfer Successful',
                'data': {
                    'credit_transfer': credit_transfer,
                }
            }

        else:
            token = Token.query.filter_by(address=contract_address).first()
            maybe_sender_transfer_account = TransferAccount.query.execution_options(show_all=True).filter_by(blockchain_address=sender_blockchain_address).first()
            maybe_sender_user = maybe_sender_transfer_account.users[0] if maybe_sender_transfer_account and len(maybe_sender_transfer_account.users) == 1 else None

            maybe_recipient_transfer_account = TransferAccount.query.execution_options(show_all=True).filter_by(blockchain_address=recipient_blockchain_address).first()
            maybe_recipient_user = maybe_recipient_transfer_account.users[0] if maybe_recipient_transfer_account and len(maybe_recipient_transfer_account.users) == 1 else None

            # Case 2: Two non-sempo users making a trade on our token. We don't have to track this!
            if not maybe_recipient_transfer_account and not maybe_sender_transfer_account:
                response_object = {
                    'message': 'No existing users involved in this transfer',
                    'data': {}
                }
            # Case 3: Two non-Sempo users, at least one of whom has interacted with Sempo users before transacting with one another
            # We don't have to track this either!
            elif (
                    # The recipient is either an external transfer account we've seen before
                    # OR we haven't seen them before and so can infer they're external
                    (
                            (
                             maybe_recipient_transfer_account
                             and maybe_recipient_transfer_account.account_type == TransferAccountType.EXTERNAL
                            ) or not maybe_recipient_transfer_account)
                    and
                    #
                    # And the sender is either an external transfer account we've seen before
                    # OR we haven't seen them before and so can infer they're external
                    ((
                             maybe_sender_transfer_account
                             and maybe_sender_transfer_account.account_type == TransferAccountType.EXTERNAL
                     ) or not maybe_sender_transfer_account)
            ):
                    response_object = {
                        'message': 'Only external users involved in this transfer',
                        'data': {}
                    }
            # Case 4: One or both of the transfer accounts are affiliated with Sempo accounts. 
            # This is the only case where we want to generate a new CreditTransfer object.
            else:
                send_transfer_account = create_transfer_account_if_required(sender_blockchain_address, token, TransferAccountType.EXTERNAL)
                receive_transfer_account = create_transfer_account_if_required(recipient_blockchain_address, token, TransferAccountType.EXTERNAL)
                transfer = CreditTransfer(
                    transfer_amount,
                    token=token,
                    sender_transfer_account=send_transfer_account,
                    recipient_transfer_account=receive_transfer_account,
                    transfer_type=TransferTypeEnum.PAYMENT,
                    sender_user=maybe_sender_user,
                    recipient_user=maybe_recipient_user,
                    require_sufficient_balance=False
                )

                transfer.resolve_as_complete_with_existing_blockchain_transaction(
                    blockchain_transaction_hash
                )

                db.session.flush()

                credit_transfer = credit_transfer_schema.dump(transfer).data
                response_object = {
                    'message': 'Transfer Successful',
                    'data': {
                        'credit_transfer': credit_transfer,
                    }
                }
        return make_response(jsonify(response_object)), 201

# add Rules for API Endpoints
credit_transfer_blueprint.add_url_rule(
    '/credit_transfer/',
    view_func=CreditTransferAPI.as_view('credit_transfer_view'),
    methods=['GET', 'POST'],
    defaults={'credit_transfer_id': None}
)

credit_transfer_blueprint.add_url_rule(
    '/credit_transfer/<int:credit_transfer_id>/',
    view_func=CreditTransferAPI.as_view('single_transfer_account_credit_transfer_view'),
    methods=['GET', 'PUT']
)

credit_transfer_blueprint.add_url_rule(
    '/credit_transfer/internal/',
    view_func=InternalCreditTransferAPI.as_view('internal_credit_transfer_view'),
    methods=['POST']
)
