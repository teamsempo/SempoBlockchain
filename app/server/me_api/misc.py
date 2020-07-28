from flask import request, g, make_response, jsonify
from flask.views import MethodView

from server import db
from server.models.feedback import Feedback
from server.models.fiat_ramp import FiatRamp, FiatRampStatusEnum, Token
from server.models.user import User
from server.utils.auth import requires_auth
from server.utils.mobile_version import check_mobile_version
from server.utils.poli_payments import PoliPaymentsError, create_poli_link, get_poli_link_status
from server.utils.credit_transfer import make_deposit_transfer
from server.utils.transfer_enums import TransferModeEnum

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


# TODO: fix this
class ReferralAPI(MethodView):
    @requires_auth
    def get(self):

        e = NotImplementedError('Referral has been updated and needs to be fixed!')

        return make_response(jsonify(str(e))), 501

        # referrals = Referral.query.filter_by(referring_user_id=g.user.id).all()
        #
        # response_object = {
        #     'message': 'Referrals Loaded',
        #     'data': {
        #         'referrals': referrals_schema.dump(referrals).data
        #     }
        # }
        #
        # return make_response(jsonify(response_object)), 201

    @requires_auth
    def post(self):
        e = NotImplementedError('Referral has been updated and needs to be fixed!')

        return make_response(jsonify(str(e))), 501

        # post_data = request.get_json()
        #
        # referral = Referral()
        #
        # referral.first_name = post_data.get('first_name')
        # referral.last_name = post_data.get('last_name')
        # referral.phone = post_data.get('phone')
        # referral.reason = post_data.get('reason')
        #
        # referral.referring_user = g.user
        #
        # db.session.add(referral)
        #
        # db.session.commit()
        #
        # response_object = {
        #     'message': 'Referral Created',
        #     'data': {
        #         'referral': referral_schema.dump(referral).data
        #     }
        # }

        # return make_response(jsonify(response_object)), 201


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
                        transfer_mode=TransferModeEnum.MOBILE,
                        fiat_ramp=fiat_ramp)

                    deposit.resolve_as_complete_and_trigger_blockchain()

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
