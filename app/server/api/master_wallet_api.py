from flask import Blueprint, request, g
from flask.views import MethodView

from server.models.token import Token
from server.models.credit_transfer import CreditTransfer
from server.models.transfer_account import TransferAccountType
from server.utils.transfer_enums import TransferTypeEnum
from server.utils.user import create_transfer_account_if_required
from server.utils.auth import requires_auth
from server.schemas import credit_transfer_schema

master_wallet_blueprint = Blueprint('master_wallet', __name__)


class MasterWalletAPI(MethodView):
    @requires_auth(allowed_roles={'ADMIN': 'superadmin'})
    def post(self):
        # Handle Parameters
        post_data = request.get_json()
        recipient_blockchain_address = post_data.get('recipient_blockchain_address', None)
        transfer_amount = post_data.get('transfer_amount', None)
        master_wallet = g.active_organisation.org_level_transfer_account
        receive_transfer_account = create_transfer_account_if_required(recipient_blockchain_address, g.active_organisation.token, TransferAccountType.EXTERNAL)

        error_message = None
        transfer_amount = int(transfer_amount)
        if not recipient_blockchain_address:
            error_message = '"recipient_blockchain_address" parameter required'
        if not transfer_amount:
            error_message = '"transfer_amount" parameter required'
        if not isinstance(transfer_amount, int):
            error_message = '"transfer_amount must be an integer'
        if not master_wallet:
            error_message = f'Organisation {g.active_organisation.id} has no master wallet'
        if error_message:
            return {'message': error_message}, 400

        transfer = CreditTransfer(
            transfer_amount,
            g.active_organisation.token,
            sender_transfer_account=master_wallet,
            recipient_transfer_account=receive_transfer_account,
            transfer_type=TransferTypeEnum.PAYMENT, # PAYMENT, since WITHDRAWAL is to the float account by definition
            require_sufficient_balance=True
        )
        # Make the transfer!
        transfer.resolve_as_complete_and_trigger_blockchain()

        credit_transfer = credit_transfer_schema.dump(transfer)
        response_object = {
            'message': 'Transfer Successful',
            'data': {
                'credit_transfer': credit_transfer,
            }
        }
        return response_object, 201


master_wallet_blueprint.add_url_rule(
    '/master_wallet/',
    view_func=MasterWalletAPI.as_view('slack_view'),
    methods=['POST']
)
