import datetime

from flask import g, make_response, jsonify, request
from flask.views import MethodView
from sqlalchemy import or_, func
from web3 import Web3

from server import db
from server.exceptions import NoTransferAccountError, UserNotFoundError, AccountNotApprovedError, \
    InsufficientBalanceError
from server.models import CreditTransfer, paginate_query, User
from server.schemas import me_credit_transfers_schema, me_credit_transfer_schema
from server.utils.auth import requires_auth, AccessControl
from server.utils.credit_transfers import check_for_any_valid_hash, find_user_with_transfer_account_from_identifiers, \
    handle_transfer_to_blockchain_address, make_payment_transfer
from server.utils.pusher import push_user_transfer_confirmation


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

        transfers, total_items, total_pages = paginate_query(transfers_query, CreditTransfer)

        transfer_list = me_credit_transfers_schema.dump(transfers).data

        responseObject = {
            'message': 'Successfully Loaded.',
            'items': total_items,
            'pages': total_pages,
            'data': {
                'credit_transfers': transfer_list,
            }
        }

        return make_response(jsonify(responseObject)), 201

    @requires_auth
    def post(self):

        post_data = request.get_json()

        uuid = post_data.get('uuid')
        created = post_data.get('created')

        transfer_use = post_data.get('transfer_use')

        transfer_amount = round(float(post_data.get('transfer_amount', 0)),6)

        transfer_random_key = post_data.get('transfer_random_key')

        pin = post_data.get('pin')

        nfc_serial_number = post_data.get('nfc_id')

        user_id = post_data.get('user_id')
        public_identifier = post_data.get('public_identifier')
        transfer_account_id = post_data.get('transfer_account_id')

        qr_data = post_data.get('qr_data')
        if qr_data is not None:
            qr_data = str(qr_data).strip(" ").strip("\t")

        is_sending = post_data.get('is_sending', False)

        authorised = False

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

            if len(split_qr_data) == 1:
                # No hyphen, so assume qr code encode the public serial number

                counterparty_user = User.query.filter(
                    func.lower(User.public_serial_number) == func.lower(qr_data)).first()

            else:
                user_id = int(split_qr_data[1])

                counterparty_user = User.query.get(user_id)

                if not counterparty_user:
                    response_object = {
                        'message': 'No such user for ID {}'.format(user_id),
                        'feedback': True,
                    }
                    return make_response(jsonify(response_object)), 400


                if not is_sending:
                    transfer_amount = int(split_qr_data[0])
                    qr_hash = split_qr_data[2]

                    user_secret = counterparty_user.secret

                    if not check_for_any_valid_hash(transfer_amount, user_secret, qr_hash):
                        response_object = {
                            'message': 'Invalid QR Code',
                            'feedback': True,
                        }
                        return make_response(jsonify(response_object)), 401

                    authorised = True

        elif nfc_serial_number:
            # We treat NFC serials differently because they're automatically authorised under the current version
            counterparty_user = User.query.filter_by(nfc_serial_number=nfc_serial_number).first()
            authorised = True

            if not counterparty_user:
                response_object = {
                    'message': 'No such user for NFC serial number {}'.format(nfc_serial_number),
                    'feedback': True
                }
                return make_response(jsonify(response_object)), 400

        else:
            try:
                counterparty_user = find_user_with_transfer_account_from_identifiers(
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

                #We're sending directly to a blockchain address
                return handle_transfer_to_blockchain_address(transfer_amount,
                                                             g.user,
                                                             public_identifier.strip('ethereum:'),
                                                             transfer_use,
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
            responseObject = {
                'message': 'Not Authorised',
                'feedback': True,
            }
            return make_response(jsonify(responseObject)), 401

        if is_sending:
            send_user = g.user
            receive_user = counterparty_user

        else:
            send_user = counterparty_user
            receive_user = g.user

        if transfer_amount == 0 or transfer_amount > send_user.transfer_account.balance:

            db.session.commit()

            responseObject = {
                'message': 'Insufficient funds',
                'feedback': True,
            }
            return make_response(jsonify(responseObject)), 400

        try:
            transfer = make_payment_transfer(transfer_amount,send_user,receive_user,transfer_use, uuid=uuid)
        except AccountNotApprovedError as e:
            db.session.commit()

            if e.is_sender is True:
                responseObject = {
                    'message': "Sender is not approved",
                    'feedback': True,
                }
                return make_response(jsonify(responseObject)), 400
            elif e.is_sender is False:
                responseObject = {
                    'message': "Recipient is not approved",
                    'feedback': True,
                }
                return make_response(jsonify(responseObject)), 400
            else:
                responseObject = {
                    'message': "Account is not approved",
                    'feedback': True,
                }
                return make_response(jsonify(responseObject)), 400


        except InsufficientBalanceError as e:
            db.session.commit()

            responseObject = {
                'message': "Insufficient balance",
                'feedback': True,
            }
            return make_response(jsonify(responseObject)), 400

        if created:
            try:
                transfer.created = datetime.datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%fz")
            except ValueError as e:
                pass

        if is_sending:
            push_user_transfer_confirmation(receive_user, transfer_random_key)

        db.session.commit()

        responseObject = {
            'message': 'Payment Successful',
            'first_name': counterparty_user.first_name,
            'last_name': counterparty_user.last_name,
            'feedback': True,
            'data': {
                'credit_transfer': me_credit_transfer_schema.dump(transfer).data
            }
        }

        return make_response(jsonify(responseObject)), 201


class RequestWithdrawalAPI(MethodView):
    @requires_auth
    def post(self):
        post_data = request.get_json()

        transfer_account = g.user.transfer_account

        withdrawal_amount = abs(round(float(post_data.get('withdrawal_amount', transfer_account.balance)),6))

        transfer_account.initialise_withdrawal(withdrawal_amount)

        db.session.commit()

        responseObject = {
            'message': 'Withdrawal Requested',
        }

        return make_response(jsonify(responseObject)), 201