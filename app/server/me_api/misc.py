from flask import request, g, make_response, jsonify
from flask.views import MethodView

from server import db
from server.models.targeting_survey import TargetingSurvey
from server.models.feedback import Feedback
from server.models.referral import Referral
from server.models.fiat_ramp import FiatRamp, FiatRampStatusEnum, Token
from server.models.user import User
from server.schemas import referrals_schema, referral_schema
from server.utils.assembly_payments import create_ap_user, AssemblyPaymentsError, create_paypal_account, \
    UserIdentifierNotFoundError, create_bank_account, set_user_disbursement_account
from server.utils.auth import requires_auth
from server.utils.mobile_version import check_mobile_version
from server.utils.poli_payments import PoliPaymentsError, create_poli_link, get_poli_link_status, generate_poli_link_from_url_token
from server.utils.credit_transfer import make_deposit_transfer, find_user_with_transfer_account_from_identifiers


class MeFeedbackAPI(MethodView):
    @requires_auth
    def post(self):
        post_data = request.get_json()

        rating = post_data.get('rating')

        if rating is None:

            response_object = {
                'message': 'No rating provided',
            }

            return make_response(jsonify(response_object)), 400

        rating = float(rating)

        question = post_data.get('question', None)
        additional_information = post_data.get('additional_information', None)

        feedback = Feedback(question=question, rating=rating, additional_information=additional_information)

        db.session.add(feedback)

        feedback.user = g.user

        db.session.commit()

        response_object = {
            'message': 'Feedback Received',
        }

        return make_response(jsonify(response_object)), 201


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

        response_object = {
            'message': 'Survey Created',
        }

        return make_response(jsonify(response_object)), 201


class ReferralAPI(MethodView):
    @requires_auth
    def get(self):

        referrals = Referral.query.filter_by(referring_user_id=g.user.id).all()

        response_object = {
            'message': 'Referrals Loaded',
            'data': {
                'referrals': referrals_schema.dump(referrals).data
            }
        }

        return make_response(jsonify(response_object)), 201

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

        response_object = {
            'message': 'Referral Created',
            'data': {
                'referral': referral_schema.dump(referral).data
            }
        }

        return make_response(jsonify(response_object)), 201


class VersionAPI(MethodView):
    def post(self):
        post_data = request.get_json()
        version = post_data.get('version')

        if version is None:
            response_object = {
                'message': 'No version provided',
            }

            return make_response(jsonify(response_object)), 400

        response_object = {
            'version': version,
            'action': check_mobile_version(version)
        }

        return make_response(jsonify(response_object)), 201


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


class PoliPaymentsAPI(MethodView):
    @requires_auth
    def put(self):
        put_data = request.get_json()
        reference = put_data.get('reference')

        if reference:

            fiat_ramp = FiatRamp.query.filter_by(payment_reference=reference).first()
            if fiat_ramp is None:
                return make_response(jsonify({'message': 'Could not find payment for reference {}'.format(reference)})), 400

            poli_link_url_token = fiat_ramp.payment_metadata['poli_link_url_token']
            try:
                get_poli_link_status_response = get_poli_link_status(poli_link_url_token=poli_link_url_token)

            except PoliPaymentsError as e:
                response_object = {
                    'message': str(e)
                }
                return make_response(jsonify(response_object)), 400

            status = get_poli_link_status_response['status']

            if fiat_ramp.payment_status == FiatRampStatusEnum.PENDING:
                if status == 'Completed':
                    # "The full amount has been paid"
                    individual_recipient_user = User.query.execution_options(show_all=True).get(fiat_ramp.authorising_user_id)
                    deposit = make_deposit_transfer(
                        transfer_amount=fiat_ramp.payment_amount,
                        token=fiat_ramp.token,
                        receive_account=individual_recipient_user,
                        fiat_ramp=fiat_ramp)

                    deposit.resolve_as_completed()

                else:
                    # The POLi link failed for some reason.
                    # e.g. Unused, Activated, PartPaid, Future
                    fiat_ramp.payment_status = FiatRampStatusEnum.FAILED
                    fiat_ramp.payment_metadata = {'poli_link_url_token': poli_link_url_token, 'reason': status}

            else:
                return make_response(jsonify({'message': 'Transfer Already Updated.'})), 400

            response_object = {
                'message': 'Updated POLi Link Status',
                'data': get_poli_link_status_response
            }

            return make_response(jsonify(response_object)), 200

        else:
            return make_response(jsonify({'message': 'Must provide POLi Link to get status'})), 400

    @requires_auth
    def post(self):
        post_data = request.get_json()
        amount = post_data.get('amount')
        token_id = post_data.get('token_id')

        if amount is None or token_id is None:
            return make_response(jsonify({'message': 'Must provide amount and token_id to generate POLi Link'})), 400

        token = Token.query.get(token_id)

        if token is None:
            return make_response(jsonify({'message': 'No token for ID {}'.format(token_id)})), 400

        if token.symbol != 'AUD':
            return make_response(jsonify({'message': 'POLi payments only support AUD'})), 400

        fiat_ramp = FiatRamp(
            payment_method='POLI',
            payment_amount=int(amount),
        )

        try:
            create_poli_link_response = create_poli_link(
                amount=amount,
                reference=fiat_ramp.payment_reference,
                currency=token.symbol,
            )

        except PoliPaymentsError as e:
            response_object = {
                'message': str(e),
            }
            return make_response(jsonify(response_object)), 400

        # converts "https://poli.to/XNSBV" into XNSBV to save in DB
        fiat_ramp.payment_metadata = {'poli_link_url_token': create_poli_link_response['poli_link'].split('/')[-1]}

        fiat_ramp.token = token

        db.session.add(fiat_ramp)

        response_object = {
            'message': 'Created POLi Link',
            'data': create_poli_link_response
        }

        return make_response(jsonify(response_object)), 201
