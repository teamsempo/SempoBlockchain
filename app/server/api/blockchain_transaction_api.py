from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView

from server import db, bt
from server.models.credit_transfer import CreditTransfer
from server.models.blockchain_transaction import BlockchainTransaction
from server.utils.blockchain_transaction import add_full_transaction_details, claim_nonce
from server.utils.auth import requires_auth

blockchain_transaction_blueprint = Blueprint('make_blockchain_transaction', __name__)

class BlockchainTransactionAPI(MethodView):

    @requires_auth(allowed_basic_auth_types=('internal'))
    def get(self):
        """
        :return: list of bitcoin transactions with outputs that have not yet been identified as spent
        """
        txns_with_unspent = (BlockchainTransaction.query
                             .filter_by(is_bitcoin=True)
                             .filter_by(status='SUCCESS')
                             .filter_by(has_output_txn=False)
                             .all())

        txn_dict = {}

        for txn in txns_with_unspent:
            # Has the txn come from an internal user that we should be watching?
            if txn.credit_transfer.recipient_transfer_account:

                hash = txn.hash
                recipient_add = txn.credit_transfer.recipient_transfer_account.blockchain_address.address
                txn_id = txn.id

                if hash in txn_dict:
                    txn_dict[hash][recipient_add] = txn_id
                else:
                    txn_dict[hash] = {recipient_add: txn_id}

        return make_response(jsonify({'transactions': txn_dict})), 201


    @requires_auth(allowed_basic_auth_types=('internal'))
    def post(self):

        post_data = request.get_json()

        if post_data.get('is_bitcoin'):
            response, status_code = add_full_transaction_details(
                post_data,
                method='POST',
                force_transaction_creation=post_data.get('force_transaction_creation')
            )
        else:
            response, status_code = claim_nonce(post_data)

        if status_code == 201:
            db.session.commit()

        return response, status_code


    @requires_auth(allowed_basic_auth_types=('internal'))
    def put(self):
        put_data = request.get_json()

        response, status_code = add_full_transaction_details(
            put_data,
            method='PUT',
            force_transaction_creation=put_data.get('force_transaction_creation')
        )

        if status_code == 201:
            db.session.commit()

        return response, status_code


class BlockchainTransactionRPC(MethodView):

    @requires_auth
    def post(self):

        post_data = request.get_json()

        call = post_data.get('call')

        if call == 'RETRY_TASK':
            task_uuid = post_data.get('task_uuid')

            bt.retry_task(task_uuid)

            response_object = {
                'message': 'Starting Retry Task',
            }

            return make_response(jsonify(response_object)), 200

        response_object = {
            'message': 'Call not recognised',
        }

        return make_response(jsonify(response_object)), 400


blockchain_transaction_blueprint.add_url_rule(
    '/blockchain_transaction/',
    view_func=BlockchainTransactionAPI.as_view('blockchain_transaction_view'),
    methods=['GET', 'POST', 'PUT']
)

blockchain_transaction_blueprint.add_url_rule(
    '/blockchain_transaction_rpc/',
    view_func=BlockchainTransactionRPC.as_view('blockchain_transaction_rpc_view'),
    methods=['POST']
)

