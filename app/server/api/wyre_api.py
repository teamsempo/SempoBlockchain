from flask import Blueprint, request, make_response, jsonify, g
from flask.views import MethodView
import config
from server import db
from server.utils.amazon_ses import send_bank_transfer_email, send_transfer_update_email
from server.models import KycApplication
from server.utils.auth import requires_auth
from server.utils.wyre import (
    create_transfer,
    get_account,
    get_exchange_rates,
    get_transfer,
    get_transfer_history,
    WyreError
)

wyre_blueprint = Blueprint('wyre_blueprint', __name__)


# need to manually create a wyre account on their website from the kyc application details provided.
class WyreAccountAPI(MethodView):
    @requires_auth(allowed_roles=['is_superadmin'])
    def get(self):

        # we only support MASTER (ngo) KYC application currently
        business_details = KycApplication.query.filter_by(type='MASTER').first()

        if business_details is None:
            return make_response(jsonify({'message': 'You must first create a business verification profile.'})), 400

        try:
            wyre_account = get_account(business_details.wyre_id)

        except WyreError as e:
            response_object = {
                'message': str(e),
            }
            return make_response(jsonify(response_object)), 400

        if wyre_account is None:
            return make_response(jsonify({'message': 'wyre account not found'})), 400

        response_object = {
            'message': 'Successfully loaded wyre account details',
            'data': {'wyre_account': wyre_account}
        }

        return make_response(jsonify(response_object)), 200


class WyreTransferAPI(MethodView):
    @requires_auth(allowed_roles=['is_superadmin'])
    def post(self):
        post_data = request.get_json()

        source_currency = post_data.get('source_currency')
        source_amount = post_data.get('source_amount')
        dest_amount = post_data.get('dest_amount')
        dest_currency = post_data.get('dest_currency')

        preview = post_data.get('preview')
        message = post_data.get('message')
        include_fees = post_data.get('include_fees')

        if (source_currency or dest_currency or source_amount or dest_amount) is None:
            return make_response(jsonify({'message': 'Must provide source_currency, dest_currency and either a source_amount or dest_amount'}))

        # we only support MASTER (ngo) KYC application currently
        business_details = KycApplication.query.filter_by(type='MASTER').first()

        if business_details is None:
            return make_response(jsonify({'message': 'A KYC application could not be found.'})), 400

        # only support ONE bank account currently.
        bank_wyre_id = business_details.bank_accounts[0].wyre_id

        if bank_wyre_id is None:
            return make_response(jsonify({'message': 'A bank account could not be found.'})), 400

        try:
            create_wyre_transfer = create_transfer(
                source_amount=source_amount,
                source_account=bank_wyre_id,  # only support transfers from bank account
                source_currency=source_currency,
                dest_amount=dest_amount,
                dest_address=config.ETH_OWNER_ADDRESS,
                dest_currency='DAI',  # only support DAI currently.
                preview=preview,
                message=message,
                include_fees=include_fees
            )
        except WyreError as e:
            response_object = {
                'message': str(e),
            }
            return make_response(jsonify(response_object)), 400

        if create_wyre_transfer['id'] != 'PREVIEW':
            send_bank_transfer_email(g.user.email, create_wyre_transfer['chargeInfo'])

        response_object = {
            'message': 'Wyre transfer details',
            'data': {'wyre_transfer': create_wyre_transfer}
        }

        return make_response(jsonify(response_object)), 201


class WyreExchangeAPI(MethodView):
    @requires_auth(allowed_roles=['is_superadmin'])
    def get(self):
        try:
            # default to DIVISOR format
            rates = get_exchange_rates()

        except WyreError as e:
            response_object = {
                'message': str(e),
            }
            return make_response(jsonify(response_object)), 400

        response_object = {
            'message': 'wyre exchange rates',
            'data': {'wyre_rates': rates}
        }

        return make_response(jsonify(response_object)), 200


class WyreWebhookAPI(MethodView):
    def post(self):
        # wyre webhook callback API
        post_data = request.get_json()

        subscription_id = post_data.get('subscriptionId')
        trigger = post_data.get('trigger')

        if subscription_id is None or trigger is None:
            return make_response(jsonify({'message': 'must provide subscription_id and trigger'})), 400

        transfer = None
        if trigger:
            # get wyre transfer details
            try:
                transfer = get_transfer(transfer_id=trigger)

            except WyreError as e:
                response_object = {
                    'message': str(e),
                }
                return make_response(jsonify(response_object)), 400

        if transfer:
            # email status updates for FAILED or COMPLETED Transfers.
            transfer_statuses = transfer['statusHistories']
            latest_status = [transfer for transfer in transfer_statuses if (transfer['state'] == 'FAILED' or transfer['state'] == 'COMPLETED')]
            if len(latest_status) > 0:
                send_transfer_update_email(g.user.email, transfer, latest_status[0])

        return make_response(jsonify({'message': 'Email sent!'})), 200


wyre_blueprint.add_url_rule(
    '/wyre_account/',
    view_func=WyreAccountAPI.as_view('wyre_account_view'),
    methods=['GET']
)

wyre_blueprint.add_url_rule(
    '/wyre_transfer/',
    view_func=WyreTransferAPI.as_view('wyre_transfer_view'),
    methods=['POST']
)

wyre_blueprint.add_url_rule(
    '/wyre_rates/',
    view_func=WyreExchangeAPI.as_view('wyre_exchange_view'),
    methods=['GET']
)

wyre_blueprint.add_url_rule(
    '/wyre_webhook/',
    view_func=WyreWebhookAPI.as_view('wyre_webhook_view'),
    methods=['POST']
)
