from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView

from sqlalchemy import or_

from server import db
from server.models import paginate_query, CreditTransfer, TransferTypeEnum, BlockchainAddress, BlockchainTransaction
from server.schemas import credit_transfers_schema, credit_transfer_schema, view_credit_transfers_schema
from server.utils.auth import requires_auth, AccessControl

from server.utils.credit_transfers import calculate_transfer_stats, find_user_with_transfer_account_from_identifiers
from server.utils.credit_transfers import (
    make_payment_transfer,
    make_withdrawal_transfer,
    make_disbursement_transfer,
    make_target_balance_transfer,
    make_blockchain_transfer)

from server.exceptions import NoTransferAccountError, UserNotFoundError, InsufficientBalanceError, AccountNotApprovedError, \
    InvalidTargetBalanceError, BlockchainError

credit_transfer_blueprint = Blueprint('credit_transfer', __name__)


class CreditTransferAPI(MethodView):

    @requires_auth(allowed_roles={'ADMIN': 'any'})
    def get(self, credit_transfer_id):

        transfer_account_ids = request.args.get('transfer_account_ids')
        transfer_type = request.args.get('transfer_type', 'ALL')
        get_transfer_stats = request.args.get('get_stats', False)

        transfer_list = None

        if transfer_type:
            transfer_type = transfer_type.upper()

        if credit_transfer_id:

            credit_transfer = CreditTransfer.query.get(credit_transfer_id)

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

            return make_response(jsonify(response_object)), 201

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

            transfers, total_items, total_pages = paginate_query(query, CreditTransfer)

            if get_transfer_stats:
                transfer_stats = calculate_transfer_stats(total_time_series=True)
            else:
                transfer_stats = None

            if g.user.roles:
                transfer_list = credit_transfers_schema.dump(transfers).data
            elif g.user.has_admin_role:
                transfer_list = view_credit_transfers_schema.dump(transfers).data

            response_object = {
                'status': 'success',
                'message': 'Successfully Loaded.',
                'items': total_items,
                'pages': total_pages,
                'data': {
                    'credit_transfers': transfer_list,
                    'transfer_stats': transfer_stats
                }
            }

            return make_response(jsonify(response_object)), 201

    @requires_auth(allowed_roles={'ADMIN': 'admin'})
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

        if action == 'COMPLETE':
            credit_transfer.resolve_as_completed()

        elif action == 'REJECT':
            credit_transfer.resolve_as_rejected()

        db.session.commit()

        response_object = {
            'message': 'Modification successful',
            'data': {
                'credit_transfer': credit_transfer_schema.dump(credit_transfer).data,
            }
        }

        return make_response(jsonify(response_object)), 201

    @requires_auth(allowed_roles={'ADMIN': 'admin'})
    def post(self, credit_transfer_id):

        post_data = request.get_json()

        uuid = post_data.get('uuid')

        transfer_type = post_data.get('transfer_type')
        transfer_amount = abs(round(float(post_data.get('transfer_amount') or 0),6))
        target_balance = post_data.get('target_balance')

        transfer_use = post_data.get('transfer_use')

        sender_user_id = post_data.get('sender_user_id')
        recipient_user_id = post_data.get('recipient_user_id')

        # These could be phone numbers, email, nfc serial numbers, card numbers etc
        sender_public_identifier = post_data.get('sender_public_identifier')
        recipient_public_identifier = post_data.get('recipient_public_identifier')

        sender_transfer_account_id = post_data.get('sender_transfer_account_id')
        recipient_transfer_account_id = post_data.get('recipient_transfer_account_id')

        recipient_transfer_accounts_ids = post_data.get('recipient_transfer_accounts_ids')
        credit_transfers = []
        response_list = []
        is_bulk = False

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

            if transfer_type not in ["DISBURSEMENT", "BALANCE"]:
                response_object = {
                    'message': 'Bulk transfer must be either disbursement or balance',
                }
                return make_response(jsonify(response_object)), 400

            transfer_user_list = []
            for transfer_account_id in recipient_transfer_accounts_ids:
                try:
                    individual_sender_user = None
                    individual_recipient_user = find_user_with_transfer_account_from_identifiers(
                        None, None, transfer_account_id)

                    transfer_user_list.append((individual_sender_user, individual_recipient_user))

                except (NoTransferAccountError, UserNotFoundError) as e:
                    response_list.append({'status': 400, 'message': str(e)})

        else:
            try:
                individual_sender_user = find_user_with_transfer_account_from_identifiers(
                    sender_user_id,
                    sender_public_identifier,
                    sender_transfer_account_id)

                individual_recipient_user = find_user_with_transfer_account_from_identifiers(
                    recipient_user_id,
                    recipient_public_identifier,
                    recipient_transfer_account_id)

                transfer_user_list = [(individual_sender_user, individual_recipient_user)]

            except (NoTransferAccountError, UserNotFoundError) as e:
                response_object = {
                    'message': str(e),
                }
                return make_response(jsonify(response_object)), 400

            if not CreditTransfer.check_has_correct_users_for_transfer_type(
                    transfer_type, individual_sender_user, individual_recipient_user):

                response_object = {
                    'message': 'For transfer type {}, wrong  users of {} and {}'.format(
                        transfer_type,
                        individual_sender_user,
                        individual_recipient_user)
                }
                return make_response(jsonify(response_object)), 400

        for sender_user, recipient_user in transfer_user_list:

            try:
                if transfer_type == 'PAYMENT':
                    transfer = make_payment_transfer(
                        transfer_amount, sender_user, recipient_user, transfer_use, uuid=uuid)

                elif transfer_type == 'WITHDRAWAL':
                    transfer = make_withdrawal_transfer(transfer_amount, sender_user, uuid=uuid)

                elif transfer_type == 'DISBURSEMENT':
                    transfer = make_disbursement_transfer(transfer_amount, recipient_user, uuid=uuid)

                elif transfer_type == 'BALANCE':
                    transfer = make_target_balance_transfer(target_balance, recipient_user, uuid=uuid)

            except (InsufficientBalanceError,
                    AccountNotApprovedError,
                    InvalidTargetBalanceError,
                    BlockchainError,
                    Exception) as e:

                if is_bulk:
                    response_list.append({'status': 400, 'message': str(e)})

                else:
                    db.session.commit()
                    response_object = {'message': str(e),}
                    return make_response(jsonify(response_object)), 400

            else:
                if is_bulk:
                    credit_transfers.append(transfer)
                    db.session.commit()

                    response_list.append({'status': 200, 'message': 'Transfer Successful'})

                else:

                    db.session.commit()
                    credit_transfer = credit_transfer_schema.dump(transfer).data

                    response_object = {
                        'message': 'Transfer Successful',
                        'data': {
                            'credit_transfer': credit_transfer,
                        }
                    }
                    return make_response(jsonify(response_object)), 201

        db.session.commit()

        response_object = {
            'message': 'Bulk Transfer Creation Successful',
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

            withdrawal.resolve_as_completed()

            credit_transfers.append(CreditTransfer.query.get(withdrawal_id_string))

        db.session.commit()

        response_object = {
            'message': 'Withdrawal Confirmed',
            'data': {
                'credit_transfers': credit_transfers_schema.dump(credit_transfers).data,
            }
        }

        return make_response(jsonify(response_object)), 201

class InternalCreditTransferAPI(MethodView):

    @requires_auth
    def post(self):
        post_data = request.get_json()

        transfer_amount = abs(round(float(post_data.get('transfer_amount') or 0),6))

        sender_blockchain_address = post_data.get('sender_blockchain_address')
        recipient_blockchain_address = post_data.get('recipient_blockchain_address')
        blockchain_transaction_hash = post_data.get('blockchain_transaction_hash')

        if BlockchainTransaction.query.filter_by(hash=blockchain_transaction_hash).first():
            response_object = {
                'message': 'Transaction hash already used',
            }
            return make_response(jsonify(response_object)), 400

        send_address_obj = (BlockchainAddress.query
                            .filter_by(address=sender_blockchain_address)
                            .first())

        receive_address_obj = (BlockchainAddress.query
                            .filter_by(address=recipient_blockchain_address)
                            .first())

        if not send_address_obj and not receive_address_obj:
            response_object = {
                'message': 'Neither sender nor receiver found for {} and {}'.format(sender_blockchain_address,
                                                                                    recipient_blockchain_address),
            }
            return make_response(jsonify(response_object)), 404

        # TODO: Handle inbounds to master wallet
        transfer = make_blockchain_transfer(transfer_amount,
                                            sender_blockchain_address,
                                            recipient_blockchain_address,
                                            existing_blockchain_txn=blockchain_transaction_hash,
                                            require_sufficient_balance=False)

        db.session.commit()
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