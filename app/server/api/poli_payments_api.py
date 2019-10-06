from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView
from server import db
from server.utils.poli_payments import PoliPaymentsError, get_poli_link_status, get_poli_link_from_token
from server.models import FiatRamp, FiatRampStatusEnum
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql.expression import cast

poli_payments_blueprint = Blueprint('poli_payments_blueprint', __name__)


class PoliPaymentWebhookAPI(MethodView):
    def post(self):
        """
        POLi Payments Webhook that provides a token to lookup a POLi link and check status.

        :return:
        """
        post_data = request.get_json()

        if post_data:
            try:
                response = get_poli_link_from_token(token=post_data)

            except PoliPaymentsError as e:
                response_object = {
                    'message': str(e)
                }
                return make_response(jsonify(response_object)), 400

            if response.status_code == 200:
                # get POLi status
                poli_link = response.poli_link
                try:
                    get_poli_link_status_response = get_poli_link_status(
                        poli_link=poli_link
                    )

                except PoliPaymentsError as e:
                    response_object = {
                        'message': str(e)
                    }
                    return make_response(jsonify(response_object)), 400

                fiat_ramp = db.query(FiatRamp).filter(
                    FiatRamp.payment_metadata["poli_link"] == cast(poli_link, JSON)
                ).first()

                if fiat_ramp is None:
                    return make_response(jsonify({'message': 'Could not find payment for POLi Link: {}'.format(poli_link)})), 400

                status = get_poli_link_status_response['status']

                if status == 'Completed':
                    # Complete: "The full amount has been paid"
                    # todo: handle internal transfer from float wallet...
                    fiat_ramp(payment_status=FiatRampStatusEnum.COMPLETE)

                else:
                    # The POLi link failed for some reason.
                    # e.g. Unused, Activated, PartPaid, Future
                    fiat_ramp(
                        payment_status=FiatRampStatusEnum.FAILED,
                        payment_metadata={'poli_link': poli_link, 'reason': status}
                    )

                response_object = {
                    'message': 'POLi Link Status',
                    'data': get_poli_link_status_response
                }

                return make_response(jsonify(response_object)), 200

        else:
            return make_response(jsonify({'message', 'No post data???'})), 400
