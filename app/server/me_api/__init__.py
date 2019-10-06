from flask import Blueprint

from server.me_api.transfer_account import MeTransferAccountAPI
from server.me_api.credit_transfer import MeCreditTransferAPI, RequestWithdrawalAPI
from server.me_api.me import MeAPI
from server.me_api.misc import MeFeedbackAPI, TargetingSurveyAPI, ReferralAPI, VersionAPI, AssemblyPaymentsUserAPI, \
    AssemblyPaymentsPayoutAccountAPI, PoliPaymentsAPI

me_blueprint = Blueprint('me', __name__)

# add Rules for API Endpoints
me_blueprint.add_url_rule(
    '/',
    view_func=MeAPI.as_view('me'),
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

me_blueprint.add_url_rule(
    '/transfer_account/',
    view_func=MeTransferAccountAPI.as_view('me_transfer_account_view'),
    methods=['GET']
)

me_blueprint.add_url_rule(
    '/poli_payments/',
    view_func=PoliPaymentsAPI.as_view('poli_payments_view'),
    methods=['POST'],
)
