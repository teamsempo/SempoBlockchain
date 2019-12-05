from flask import Blueprint

from server.me_api.transfer_account import MeTransferAccountAPI
from server.me_api.credit_transfer import MeCreditTransferAPI, RequestWithdrawalAPI
from server.me_api.me import MeAPI
from server.me_api.misc import (
    MeFeedbackAPI,
    ReferralAPI,
    VersionAPI,
    PoliPaymentsAPI
)

from server.me_api.exchange import ExchangeAPI

me_blueprint = Blueprint('me', __name__)

# add Rules for API Endpoints
me_blueprint.add_url_rule(
    '/',
    view_func=MeAPI.as_view('me'),
    methods=['GET']
)

me_blueprint.add_url_rule(
    '/exchange/',
    view_func=ExchangeAPI.as_view('exchange_api_view'),
    methods=['GET', 'POST'],
    defaults={'exchange_id': None}
)

me_blueprint.add_url_rule(
    '/exchange/<int:exchange_id>/',
    view_func=ExchangeAPI.as_view('single_exchange_api_view'),
    methods=['GET']
)


me_blueprint.add_url_rule(
    '/credit_transfer/',
    view_func=MeCreditTransferAPI.as_view('me_transfer_view'),
    methods=['GET', 'POST']
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
    '/transfer_account/',
    view_func=MeTransferAccountAPI.as_view('me_transfer_account_view'),
    methods=['GET']
)

me_blueprint.add_url_rule(
    '/poli_payments/',
    view_func=PoliPaymentsAPI.as_view('poli_payments_view'),
    methods=['PUT', 'POST'],
)
