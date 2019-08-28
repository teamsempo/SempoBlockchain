from flask import Blueprint, request, make_response, jsonify, g, session
from flask.views import MethodView

from server import basic_auth, db, celery_app
from server.models import BlockchainTransaction, CreditTransfer
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

        if call == 'CREATE_RESPONSE':

            transaction_hash = post_data.get('transaction_hash')

            if transaction_hash is None:
                response_object = {
                    'message': 'No transaction hash supplied',
                }

                return make_response(jsonify(response_object)), 400

            transaction = BlockchainTransaction.query.filter_by(hash=transaction_hash).first()
            if transaction is None:
                response_object = {
                    'message': 'Transaction not found for hash {}'.format(transaction_hash),
                }

                return make_response(jsonify(response_object)), 405

            credit_transfer_id = transaction.credit_transfer_id

            if credit_transfer_id is None:
                response_object = {
                    'message': 'No credit transfer id for hash {}'.format(transaction_hash),
                }

                return make_response(jsonify(response_object)), 404

            blockchain_task = celery_app.signature('worker.celery_tasks.create_transaction_response',
                                                   kwargs={'previous_result': {'transaction_hash': transaction_hash},
                                                           'credit_transfer_id': credit_transfer_id
                                                           })
            blockchain_task.delay()

            response_object = {
                'message': 'Starting Create Response',
            }

            return make_response(jsonify(response_object)), 200

        elif call =='COMPLETE_TASKS':

            credit_transfer_id = post_data.get('credit_transfer_id')

            if credit_transfer_id is None:
                response_object = {
                    'message': 'No credit transfer id supplied',
                }

                return make_response(jsonify(response_object)), 400

            credit_transfer = CreditTransfer.query.get(credit_transfer_id)

            if credit_transfer is None:
                response_object = {
                    'message': 'No credit transfer not found',
                }

                return make_response(jsonify(response_object)), 404

            credit_transfer.send_blockchain_payload_to_worker(is_retry=True)

            response_object = {
                'message': 'Starting Complete Tasks',
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

