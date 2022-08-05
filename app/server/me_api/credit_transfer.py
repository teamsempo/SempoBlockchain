import datetime

from flask import g, make_response, jsonify, request
from flask.views import MethodView
from sqlalchemy import or_
from web3 import Web3
from decimal import Decimal

from server import db
from server.exceptions import (
    NoTransferAccountError,
    UserNotFoundError,
    AccountNotApprovedError,
    InsufficientBalanceError,
    TransferAmountLimitError
)
from server.models.user import User
from server.models.transfer_card import TransferCard
from server.models.transfer_card_state import TransferCardState
from server.models.transfer_account import TransferAccount
from server.models.credit_transfer import CreditTransfer
from server.utils.transfer_enums import TransferModeEnum
from server.models.utils import paginate_query
from server.schemas import me_credit_transfers_schema, me_credit_transfer_schema
from server.utils.auth import requires_auth, show_all
from server.utils.access_control import AccessControl
from server.utils.credit_transfer import (
    check_for_any_valid_hash,
    find_user_with_transfer_account_from_identifiers,
    handle_transfer_to_blockchain_address,
    make_payment_transfer
)
from server.utils.pusher_utils import push_user_transfer_confirmation
from server.utils.transfer_account import find_transfer_accounts_with_matching_token


class MeCreditTransferAPI(MethodView):
    @requires_auth
    def get(self):

        user = g.user

        if AccessControl.has_suffient_role(user.roles, {'ADMIN': 'subadmin', 'VENDOR': 'supervendor'}):
            # admins and supervendors see all transfers for that transfer account
            transfer_account = user.transfer_account

            transfers_query = CreditTransfer.query.filter(
                or_(CreditTransfer.recipient_transfer_account_id == transfer_account.id,
                    CreditTransfer.sender_transfer_account_id == transfer_account.id))

        else:
            # other users only see transfers involving themselves
            transfers_query = CreditTransfer.query.filter(
                or_(CreditTransfer.recipient_user_id == user.id,
                    CreditTransfer.sender_user_id == user.id))

        transfers, total_items, total_pages, new_last_fetched = paginate_query(transfers_query)

        transfer_list = me_credit_transfers_schema.dump(transfers).data

        response_object = {
            'message': 'Successfully Loaded.',
            'items': total_items,
            'pages': total_pages,
            'last_fetched': new_last_fetched,
            'data': {
                'credit_transfers': transfer_list,
            }
        }

        return make_response(jsonify(response_object)), 201

    @show_all
    @requires_auth
    def post(self):

        post_data = request.get_json()

        uuid = post_data.get('uuid')
        created = post_data.get('created')

        transfer_use = post_data.get('transfer_use')
        try:
            use_ids = transfer_use.split(',')  # passed as '3,4' etc.
        except AttributeError:
            use_ids = transfer_use
        transfer_mode = post_data.get('transfer_mode')

        transfer_amount = round(Decimal(post_data.get('transfer_amount', 0)), 6)

        transfer_random_key = post_data.get('transfer_random_key')

        pin = post_data.get('pin')

        nfc_serial_number = post_data.get('nfc_id')
        # In the future we can reject payloads with missing session numbers. For now, it's just a sentinel -1
        nfc_session_number = post_data.get('nfc_session_number', -1) 
        amount_loaded = post_data.get('amount_loaded', -1) 
        amount_deducted = post_data.get('amount_deducted', -1) 

        user_id = post_data.get('user_id')
        public_identifier = post_data.get('public_identifier')
        transfer_account_id = post_data.get('transfer_account_id')

        qr_data = post_data.get('qr_data')
        if qr_data is not None:
            qr_data = str(qr_data).strip(" ").strip("\t")

        my_transfer_account_id = post_data.get("my_transfer_account_id")

        is_sending = post_data.get('is_sending', False)

        transfer_card = None
        my_transfer_account = None
        transfer_card_state = None
    
        authorised = False
        if transfer_account_id:
            counterparty_transfer_account = TransferAccount.query.get(transfer_account_id)
        else:
            counterparty_transfer_account = None

        if uuid:
            existing_transfer = CreditTransfer.query.filter_by(uuid=uuid).first()

            if existing_transfer:
                # We return a 201 here so that the client removes the uuid from the cache
                response_object = {
                    'message': 'Transfer already in cache',
                    'data': {
                        'credit_transfer': me_credit_transfer_schema.dump(existing_transfer).data,
                    }
                }
                return make_response(jsonify(response_object)), 201

        if qr_data:

            split_qr_data = qr_data.split('-')

            transfer_amount = int(split_qr_data[0])
            transfer_account_id = int(split_qr_data[1])
            user_id = int(split_qr_data[2])
            qr_hash = split_qr_data[3]

            counterparty_user = User.query.get(user_id)

            if not counterparty_user:
                response_object = {
                    'message': 'No such user for ID {}'.format(user_id),
                    'feedback': True,
                }
                return make_response(jsonify(response_object)), 404

            counterparty_transfer_account = TransferAccount.query.get(transfer_account_id)

            if not counterparty_transfer_account:
                response_object = {
                    'message': 'No such Transfer Account for ID {}'.format(transfer_account_id),
                    'feedback': True,
                }
                return make_response(jsonify(response_object)), 404

            if counterparty_transfer_account not in counterparty_user.transfer_accounts:
                if not counterparty_transfer_account:
                    response_object = {
                        'message': 'User {} not authorised for Transfer Account {}.'
                            .format(user_id, transfer_account_id),
                        'feedback': True,
                    }
                    return make_response(jsonify(response_object)), 401

            my_transfer_account = find_transfer_accounts_with_matching_token(
                g.user, counterparty_transfer_account.token
            )

            user_secret = counterparty_user.secret

            if not check_for_any_valid_hash(transfer_amount, transfer_account_id, user_secret, qr_hash):
                response_object = {
                    'message': 'Invalid QR Code',
                    'feedback': True,
                }
                return make_response(jsonify(response_object)), 401

            authorised = True

        elif nfc_serial_number:
            # We treat NFC serials differently because they're automatically authorized under the current version
            transfer_card = TransferCard.query.filter_by(nfc_serial_number=nfc_serial_number).first()
            if transfer_card:
                counterparty_user = transfer_card.user
                counterparty_transfer_account = transfer_card.transfer_account

            if not transfer_card or not counterparty_user or not counterparty_transfer_account:
                response_object = {
                    'message': 'Card not found',
                    'feedback': True
                }
                return make_response(jsonify(response_object)), 404
            # Add NFC usage object. This is created _before_ the transfer, because want to store usages even
            # if the transfer is failed/rejected for any reason. 
            transfer_card_state = TransferCardState(
                vendor_transfer_account=my_transfer_account,
                transfer_card=transfer_card,
                session_number=nfc_session_number,
                amount_deducted = amount_deducted,
                amount_loaded=amount_loaded
            )
            db.session.add(transfer_card_usage)
            authorised = True

        else:
            try:
                counterparty_user, _ = find_user_with_transfer_account_from_identifiers(
                    user_id,
                    public_identifier,
                    transfer_account_id)

            except (NoTransferAccountError, UserNotFoundError) as e:

                if not Web3.isAddress(public_identifier.strip('ethereum:')) or not is_sending:
                    response_object = {
                        'message': str(e),
                        'feedback': True
                    }
                    return make_response(jsonify(response_object)), 400

                my_transfer_account = TransferAccount.query.get(my_transfer_account_id)

                if not my_transfer_account:
                    response_object = {
                        'message': 'Transfer Account not found for my_transfer_account_id {}'.format(
                            my_transfer_account_id)
                    }
                    return make_response(jsonify(response_object)), 400

                #We're sending directly to a blockchain address
                return handle_transfer_to_blockchain_address(transfer_amount,
                                                             my_transfer_account,
                                                             public_identifier.strip('ethereum:'),
                                                             transfer_use,
                                                             transfer_mode=TransferModeEnum.EXTERNAL,
                                                             uuid=uuid)

            if not counterparty_user:
                response_object = {
                    'message': 'User not found',
                    'feedback': True
                }
                return make_response(jsonify(response_object)), 400

            authorised = counterparty_user.verify_password(str(pin))

        if is_sending:
            authorised = True

        if not authorised:
            response_object = {
                'message': 'Not Authorised',
                'feedback': True,
            }
            return make_response(jsonify(response_object)), 401

        if not my_transfer_account:
            if not my_transfer_account_id:
                response_object = {
                    'message': 'You must provide your Transfer Account ID',
                }
                return make_response(jsonify(response_object)), 400

            my_transfer_account = TransferAccount.query.get(my_transfer_account_id)

            if not my_transfer_account:
                response_object = {
                    'message': 'Transfer Account not found for my_transfer_account_id {}'.format(my_transfer_account_id)
                }
                return make_response(jsonify(response_object)), 400

        if my_transfer_account not in g.user.transfer_accounts:
            response_object = {
                'message': 'Transfer account provided does not belong to user',
            }
            return make_response(jsonify(response_object)), 401

        if is_sending:
            send_user = g.user
            send_transfer_account = my_transfer_account
            receive_user = counterparty_user
            receive_transfer_account = counterparty_transfer_account

        else:
            if counterparty_transfer_account is None:
                response_object = {
                    'message': 'Counterparty Transfer Account not specified'
                }
                return make_response(jsonify(response_object)), 400

            send_user = counterparty_user
            send_transfer_account = counterparty_transfer_account
            receive_user = g.user
            receive_transfer_account = my_transfer_account

        if not transfer_card and (transfer_amount == 0 or transfer_amount > send_transfer_account.balance):

            db.session.commit()

            response_object = {
                'message': 'Insufficient funds',
                'feedback': True,
            }
            return make_response(jsonify(response_object)), 400

        try:
            if transfer_card_usage: transfer_card_usage.vendor_transfer_account = my_transfer_account
            transfer = make_payment_transfer(transfer_amount=transfer_amount,
                                             send_user=send_user,
                                             send_transfer_account=send_transfer_account,
                                             receive_user=receive_user,
                                             receive_transfer_account=receive_transfer_account,
                                             transfer_use=transfer_use,
                                             transfer_mode=transfer_mode,
                                             uuid=uuid,
                                             transfer_card=transfer_card,
                                             transfer_card_state=transfer_card_state,
                                             require_sufficient_balance=False)

        except AccountNotApprovedError as e:
            db.session.commit()

            if e.is_sender is True:
                response_object = {
                    'message': "Sender is not approved",
                    'feedback': True,
                }
                return make_response(jsonify(response_object)), 400
            elif e.is_sender is False:
                response_object = {
                    'message': "Recipient is not approved",
                    'feedback': True,
                }
                return make_response(jsonify(response_object)), 400
            else:
                response_object = {
                    'message': "Account is not approved",
                    'feedback': True,
                }
                return make_response(jsonify(response_object)), 400


        except InsufficientBalanceError as e:
            db.session.commit()

            response_object = {
                'message': "Insufficient balance",
                'feedback': True,
            }
            return make_response(jsonify(response_object)), 400

        except TransferAmountLimitError as e:
            db.session.commit()
            response_object = {
                'message': "Account limit reached",
                'feedback': True,
            }
            return make_response(jsonify(response_object)), 400

        except Exception as e:
            db.session.commit()
            response_object = {
                'message': "Unknown Error",
                'feedback': True,
            }
            return make_response(jsonify(response_object)), 400

        if created:
            try:
                transfer.created = datetime.datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%fz")
            except ValueError as e:
                pass

        if is_sending:
            push_user_transfer_confirmation(receive_user, transfer_random_key)

        db.session.commit()

        response_object = {
            'message': 'Payment Successful',
            'first_name': counterparty_user.first_name,
            'last_name': counterparty_user.last_name,
            'feedback': True,
            'data': {
                'credit_transfer': me_credit_transfer_schema.dump(transfer).data
            }
        }

        return make_response(jsonify(response_object)), 201


class RequestWithdrawalAPI(MethodView):
    @requires_auth
    def post(self):
        post_data = request.get_json()

        transfer_account = g.user.transfer_account

        withdrawal_amount = abs(round(Decimal(post_data.get('withdrawal_amount', transfer_account.balance)),6))

        transfer_account.initialise_withdrawal(withdrawal_amount, transfer_mode=TransferModeEnum.MOBILE)

        db.session.commit()

        response_object = {
            'message': 'Withdrawal Requested',
        }

        return make_response(jsonify(response_object)), 201