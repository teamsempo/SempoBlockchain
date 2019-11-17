from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView
from server import db
from server.utils.poli_payments import PoliPaymentsError, get_poli_link_status, get_poli_link_url_token_from_transaction_token, generate_poli_link_from_url_token
from server.models.fiat_ramp import FiatRamp, FiatRampStatusEnum
from server.models.user import User
from server.utils.credit_transfer import make_deposit_transfer, find_user_with_transfer_account_from_identifiers

poli_payments_blueprint = Blueprint('poli_payments_blueprint', __name__)


class PoliPaymentWebhookAPI(MethodView):
    def post(self):
        """
        POLi Payments Webhook that provides a token to lookup a POLi link and check status.
        :return:
        """

        if request.data:
            try:
                response = get_poli_link_url_token_from_transaction_token(token=request.data.decode())

            except PoliPaymentsError as e:
                response_object = {
                    'message': str(e)
                }
                return make_response(jsonify(response_object)), 400

            poli_link_url_token = response['poli_link_url_token']
            try:
                get_poli_link_status_response = get_poli_link_status(
                    poli_link_url_token=poli_link_url_token
                )

            except PoliPaymentsError as e:
                response_object = {
                    'message': str(e)
                }
                return make_response(jsonify(response_object)), 400

            fiat_ramp = db.session.query(FiatRamp).filter(
                FiatRamp.payment_metadata["poli_link_url_token"].astext == poli_link_url_token
            ).first()

            if fiat_ramp is None:
                return make_response(jsonify({'message': 'Could not find payment for POLi Link token: {}'.format(poli_link_url_token)})), 400

            status = get_poli_link_status_response['status']

            if fiat_ramp.payment_status == FiatRampStatusEnum.PENDING:
                if status == 'Completed':
                    # Complete: "The full amount has been paid"
                    individual_recipient_user = User.query.execution_options(show_all=True).get(fiat_ramp.authorising_user_id)
                    deposit = make_deposit_transfer(
                        transfer_amount=int(fiat_ramp.payment_amount),
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
                'message': 'POLi Link Status',
                'data': get_poli_link_status_response
            }

            return make_response(jsonify(response_object)), 200

        else:
            return make_response(jsonify({'message', 'No token'})), 400


poli_payments_blueprint.add_url_rule(
    '/poli_payments_webhook/',
    view_func=PoliPaymentWebhookAPI.as_view('poli_payments_webhook_view'),
    methods=['POST']
)
