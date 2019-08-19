from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView
from web3 import Web3
import datetime

from sqlalchemy import func, or_

from server import db
from server.models import paginate_query, CreditTransfer, User, Feedback, TargetingSurvey, Referral
from server.schemas import (
    me_credit_transfers_schema,
    me_credit_transfer_schema,
    user_schema,
    old_user_schema,
    referrals_schema,
    referral_schema)
from server.utils.auth import requires_auth
from server.utils.pusher import push_user_transfer_confirmation
from server.utils.credit_transfers import (
    make_payment_transfer,
    handle_transfer_to_blockchain_address,
    find_user_with_transfer_account_from_identifiers,
    check_for_any_valid_hash
)
from server.exceptions import NoTransferAccountError, UserNotFoundError, InsufficientBalanceError, AccountNotApprovedError
from server.utils.mobile_version import check_mobile_version
from server.utils.assembly_payments import (
    create_ap_user,
    create_bank_account,
    create_paypal_account,
    set_user_disbursement_account,
    UserIdentifierNotFoundError,
    AssemblyPaymentsError
)

me_blueprint = Blueprint('me', __name__)


class MeAPI(MethodView):
    @requires_auth
    def get(self):

        version = request.args.get('version', 1)

        if str(version) == '2':
            user = g.user

            responseObject = {
                'message': 'Successfully Loaded.',
                'data': {
                    'user': user_schema.dump(user).data,
                }
            }

            return make_response(jsonify(responseObject)), 201


        user = g.user

        if user.is_subadmin or user.is_supervendor:
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

        responseObject = {
            'message': 'Successfully Loaded.',
            'items': total_items,
            'pages': total_pages,
            'data': {
                'user': old_user_schema.dump(user).data,
                # 'credit_transfers': transfer_list,
            }
        }

        return make_response(jsonify(responseObject)), 201


class MeCreditTransferAPI(MethodView):
    @requires_auth
    def get(self):

        user = g.user

        if user.is_subadmin or user.is_supervendor:
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


class PreCheckAPI(MethodView):
    @requires_auth
    def get(self):
        qr_id = request.args.get('qr_id')

        if qr_id is not None:
            qr_id = str(qr_id).strip(" ").strip("\t")

        transfer_amount = abs(round(float(request.args.get('transfer_amount', 0)),6))

        beneficiary = User.query.filter(func.lower(User.public_serial_number) == func.lower(qr_id)).first()

        if beneficiary is None:

            split_qr_data = qr_id.split('-')

            if len(split_qr_data) != 1:

                user_id = split_qr_data[0]
                qr_hash = split_qr_data[1]

                beneficiary = User.query.get(int(user_id))

                if beneficiary is not None:
                    user_secret = beneficiary.secret
                    authorised = check_for_any_valid_hash(user_secret, qr_hash)

                    if not authorised:

                        responseObject = {
                            'message': 'Beneficiary Not Found'
                        }
                        return make_response(jsonify(responseObject)), 404



        if beneficiary is None or beneficiary.transfer_account is None:
            responseObject = {
                'message': 'Beneficiary Not Found'
            }
            return make_response(jsonify(responseObject)), 404

        sufficient_funds = transfer_amount < beneficiary.transfer_account.balance

        responseObject = {
            'message': 'Beneficiary Data found',
            'data': {
                'first_name': beneficiary.first_name,
                'last_name': beneficiary.last_name,
                'sufficient_funds': True
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


class MeFeedbackAPI(MethodView):
    @requires_auth
    def post(self):
        post_data = request.get_json()

        transfer_account = g.user.transfer_account

        rating = post_data.get('rating')

        if rating is None:

            responseObject = {
                'message': 'No rating provided',
            }

            return make_response(jsonify(responseObject)), 400

        rating = float(rating)

        question = post_data.get('question', None)
        additional_information = post_data.get('additional_information', None)

        feedback = Feedback(question=question, rating=rating, additional_information=additional_information)

        db.session.add(feedback)

        feedback.transfer_account = transfer_account

        db.session.commit()

        responseObject = {
            'message': 'Feedback Received',
        }

        return make_response(jsonify(responseObject)), 201


class TargetingSurveyAPI(MethodView):
    @requires_auth
    def post(self):
        post_data = request.get_json()

        targeting_survey = TargetingSurvey()

        targeting_survey.number_people_household = post_data.get('number_people_household')
        targeting_survey.number_below_adult_age_household = post_data.get('number_below_adult_age_household')
        targeting_survey.number_people_women_household = post_data.get('number_people_women_household')
        targeting_survey.number_people_men_household = post_data.get('number_people_men_household')
        targeting_survey.number_people_work_household = post_data.get('number_people_work_household')
        targeting_survey.disabilities_household = post_data.get('disabilities_household')
        targeting_survey.long_term_illnesses_household = post_data.get('long_term_illnesses_household')

        targeting_survey.user = g.user

        db.session.add(targeting_survey)

        db.session.commit()

        responseObject = {
            'message': 'Survey Created',
        }

        return make_response(jsonify(responseObject)), 201


class ReferralAPI(MethodView):
    @requires_auth
    def get(self):

        referrals = Referral.query.filter_by(referring_user_id=g.user.id).all()

        responseObject = {
            'message': 'Referrals Loaded',
            'data': {
                'referrals': referrals_schema.dump(referrals).data
            }
        }

        return make_response(jsonify(responseObject)), 201

    @requires_auth
    def post(self):
        post_data = request.get_json()

        referral = Referral()

        referral.first_name = post_data.get('first_name')
        referral.last_name = post_data.get('last_name')
        referral.phone = post_data.get('phone')
        referral.reason = post_data.get('reason')

        referral.referring_user = g.user

        db.session.add(referral)

        db.session.commit()

        responseObject = {
            'message': 'Referral Created',
            'data': {
                'referral': referral_schema.dump(referral).data
            }
        }

        return make_response(jsonify(responseObject)), 201


class VersionAPI(MethodView):
    def post(self):
        post_data = request.get_json()
        version = post_data.get('version')

        if version is None:
            responseObject = {
                'message': 'No version provided',
            }

            return make_response(jsonify(responseObject)), 400

        responseObject = {
            'version': version,
            'action': check_mobile_version(version)
        }

        return make_response(jsonify(responseObject)), 201


class AssemblyPaymentsUserAPI(MethodView):
    @requires_auth
    def post(self):
        # Assembly Payments
        # - create ap user account
        post_data = request.get_json()
        user = g.user

        email = post_data.get('email')
        mobile = post_data.get('mobile')
        first_name = post_data.get('first_name')
        last_name = post_data.get('last_name')
        dob = post_data.get('dob')
        government_number = post_data.get('government_number')

        addressline_1 = post_data.get('addressline_1')
        city = post_data.get('city')
        state = post_data.get('state')
        zip_code = post_data.get('zip_code')
        country = post_data.get('country')

        try:
            create_ap_user_response = create_ap_user(
                email=email,
                mobile=mobile,
                first_name=first_name,
                last_name=last_name,
                dob=dob,
                government_number=government_number,
                addressline_1=addressline_1,
                city=city,
                state=state,
                zip_code=zip_code,
                country=country
            )

        except AssemblyPaymentsError as e:
            response_object = {
                'message': str(e),
            }
            return make_response(jsonify(response_object)), 400

        ap_user_id = create_ap_user_response.get('users').get('id')

        if user:
            user.ap_user_id = ap_user_id
            db.session.commit()

        response_object = {
            'message': 'Created Assembly Payments User ID: {}'.format(ap_user_id),
            'data': create_ap_user_response
        }

        return make_response(jsonify(response_object)), 201


class AssemblyPaymentsPayoutAccountAPI(MethodView):
    @requires_auth
    def post(self):
        # Assembly Payments
        # - create payout account (bank account or paypal account)
        # - tie account to ap user account

        post_data = request.get_json()
        user = g.user

        bank_name = post_data.get('bank_name')
        account_name = post_data.get('account_name')
        routing_number = post_data.get('routing_number')
        account_number = post_data.get('account_number')
        account_type = post_data.get('account_type')
        holder_type = post_data.get('holder_type')
        payout_currency = post_data.get('payout_currency')
        country = post_data.get('country')

        paypal_email = post_data.get('paypal_email')

        user_id = user.ap_user_id
        create_payout_account_response = None
        ap_type = None

        if paypal_email:
            try:
                create_payout_account_response = create_paypal_account(
                    user_id=user_id,
                    paypal_email=paypal_email
                )
                ap_type = 'paypal_account'

            except (UserIdentifierNotFoundError, AssemblyPaymentsError) as e:
                response_object = {
                    'message': str(e),
                }
                return make_response(jsonify(response_object)), 400

        if bank_name:
            try:
                create_payout_account_response = create_bank_account(
                    user_id=user_id,
                    bank_name=bank_name,
                    account_name=account_name,
                    routing_number=routing_number,
                    account_number=account_number,
                    account_type=account_type,
                    holder_type=holder_type,
                    country=country,
                    payout_currency=payout_currency,
                )
                ap_type = 'bank_account'

            except (UserIdentifierNotFoundError, AssemblyPaymentsError) as e:
                response_object = {
                    'message': str(e),
                }
                return make_response(jsonify(response_object)), 400

        if ap_type is not None:
            try:
                # tie created ap bank or paypal account to ap user
                account_id = create_payout_account_response.get(ap_type+'s').get('id')
                set_user_disbursement_account(
                    user_id=user_id,
                    account_id=account_id
                )

                # submit ap_payout_account id to db
                if user and ap_type:
                    if ap_type == 'bank_account':
                        user.ap_bank_id = account_id
                    if ap_type == 'paypal_account':
                        user.ap_paypal_id = account_id

                    db.session.commit()

            except (UserIdentifierNotFoundError, AssemblyPaymentsError) as e:
                response_object = {
                    'message': str(e),
                }
                return make_response(jsonify(response_object)), 400

        response_object = {
            'message': '{} created and tied to user {}'.format(ap_type, user_id),
            'data': create_payout_account_response
        }

        return make_response(jsonify(response_object)), 201


# add Rules for API Endpoints
me_blueprint.add_url_rule(
    '/',
    view_func=MeAPI.as_view('me'),
    methods=['GET']
)

me_blueprint.add_url_rule(
    '/credit_transfer/',
    view_func=MeCreditTransferAPI.as_view('metransfers'),
    methods=['GET', 'POST']
)

me_blueprint.add_url_rule(
    '/precheck_transfer/',
    view_func=PreCheckAPI.as_view('precheck_transfer_view'),
    methods=['GET']
)

me_blueprint.add_url_rule(
    '/request_withdrawal/',
    view_func=RequestWithdrawalAPI.as_view('request_withdrawal_view'),
    methods=['POST']
)

me_blueprint.add_url_rule(
    '/feedback/',
    view_func=MeFeedbackAPI.as_view('new_feedback_view'),
    methods=['POST']
)

me_blueprint.add_url_rule(
    '/targeting_survey/',
    view_func=TargetingSurveyAPI.as_view('targeting_survey_view'),
    methods=['POST']
)

me_blueprint.add_url_rule(
    '/referral/',
    view_func=ReferralAPI.as_view('referral_view'),
    methods=['GET', 'POST']
)

me_blueprint.add_url_rule(
    '/version/',
    view_func=VersionAPI.as_view('version_view'),
    methods=['POST']
)

me_blueprint.add_url_rule(
    '/ap_user/',
    view_func=AssemblyPaymentsUserAPI.as_view('ap_user_view'),
    methods=['POST']
)

me_blueprint.add_url_rule(
    '/ap_payout_account/',
    view_func=AssemblyPaymentsPayoutAccountAPI.as_view('ap_payout_account_view'),
    methods=['POST']
)
