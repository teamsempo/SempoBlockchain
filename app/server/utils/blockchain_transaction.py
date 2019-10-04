from flask import make_response, jsonify, current_app
from sqlalchemy import or_, and_
from server.models.transfer import BlockchainTransaction, BlockchainAddress
from server.exceptions import BlockchainError
from server import db, celery_app, sentry
import datetime
import random
import time


def add_full_transaction_details(details_dict, method='POST', force_transaction_creation=False):

    transaction_id = details_dict.get('transaction_id')

    status = details_dict.get('status')
    message = details_dict.get('message')
    transaction_hash = details_dict.get('transaction_hash')
    transaction_nonce = details_dict.get('transaction_nonce')
    signing_address = details_dict.get('signing_address')
    block = details_dict.get('block')
    transaction_type = details_dict.get('transaction_type')
    submitted_date = details_dict.get('submitted_date')
    added_date = details_dict.get('added_date')

    is_bitcoin = details_dict.get('is_bitcoin')

    has_output_txn = details_dict.get('has_output_txn')

    credit_transfer_id = details_dict.get('credit_transfer_id')

    if method == 'PUT' and not force_transaction_creation:
        if transaction_id:
            blockchain_transaction = BlockchainTransaction.query.get(transaction_id)

        elif transaction_hash:

            blockchain_transaction = BlockchainTransaction.query.filter_by(hash=transaction_hash).first()
        else:
            response_object = {
                'message': 'Transaction not found'
            }

            return make_response(jsonify(response_object)), 404

    else:

        address_object = BlockchainAddress.query.filter_by(address=signing_address).first()

        if address_object:
            signing_blockchain_address_id = address_object.id
        elif force_transaction_creation:
            signing_blockchain_address_id = None
        else:
            response_object = {
                'message': 'Address not found'
            }

            return make_response(jsonify(response_object)), 404

        blockchain_transaction = BlockchainTransaction(nonce=transaction_nonce,
                                                       signing_blockchain_address_id=signing_blockchain_address_id)

        db.session.add(blockchain_transaction)
        db.session.flush()

    if status is not None and blockchain_transaction.status != "FAILED":
        blockchain_transaction.status = status
    if message is not None:
        blockchain_transaction.message = message
    if transaction_hash is not None:
        blockchain_transaction.hash = transaction_hash
    if block is not None:
        blockchain_transaction.block = block
    if added_date is not None:
        blockchain_transaction.added_date = added_date
    if submitted_date is not None:
        blockchain_transaction.submitted_date = submitted_date
    if credit_transfer_id is not None:
        blockchain_transaction.credit_transfer_id = credit_transfer_id
    if transaction_type is not None:
        blockchain_transaction.transaction_type = transaction_type
    if is_bitcoin is not None:
        blockchain_transaction.is_bitcoin = is_bitcoin
    if has_output_txn is not None:
        blockchain_transaction.has_output_txn = has_output_txn

    return make_response(jsonify({'transaction_id': blockchain_transaction.id})), 201

def claim_nonce(details_dict):
    network_nonce = details_dict.get('network_nonce', 0)
    signing_address = details_dict.get('signing_address')

    address_object = BlockchainAddress.query.filter_by(address=signing_address).first()

    if not address_object:
        response_object = {
            'message': 'Address not found'
        }

        return make_response(jsonify(response_object)), 404

    local_nonce = consecutive_success_or_pending_txn_count(address_object.id, network_nonce)

    nonce = max(network_nonce, local_nonce)

    blockchain_transaction = BlockchainTransaction(status='PENDING',
                                                   nonce=nonce,
                                                   signing_blockchain_address_id=address_object.id)

    db.session.add(blockchain_transaction)
    db.session.commit()

    gauranteed_clash_free = False

    clash_fix_attempts = 0
    while not gauranteed_clash_free and clash_fix_attempts < 200:
        clash_fix_attempts += 1
        # Occasionally two workers will hit the db at the same time and claim the same nonce

        expire_time = datetime.datetime.utcnow() - datetime.timedelta(
            seconds=current_app.config['PENDING_TRANSACTION_EXPIRY_SECONDS'])

        clashed_nonces = (BlockchainTransaction.query
                          .filter(BlockchainTransaction.created > expire_time)
                          .filter(BlockchainTransaction.id != blockchain_transaction.id)
                          .filter(BlockchainTransaction.signing_blockchain_address_id == address_object.id)
                          .filter(BlockchainTransaction.status == 'PENDING')
                          .filter(BlockchainTransaction.nonce == blockchain_transaction.nonce)
                          .order_by(BlockchainTransaction.id.asc())
                          .all())

        if len(clashed_nonces) > 0:
            # If there is a clash, just try again
            print('~~~~~~~~~~~~~~~~~~~fixing clash~~~~~~~~~~~~~~~~~~~')

            # Sleeping the process by a small random amount to force the two processes out of lockstep
            time_to_sleep = random.random()/100
            time.sleep(time_to_sleep)

            print("transaction id: " + str(blockchain_transaction.id))
            new_nonce = consecutive_success_or_pending_txn_count(address_object.id, network_nonce)
            blockchain_transaction.nonce = new_nonce
            db.session.commit()

        else:
            gauranteed_clash_free = True

    response_object = {
        'transaction_id': blockchain_transaction.id,
        'nonce': blockchain_transaction.nonce,
    }

    return make_response(jsonify(response_object)), 201


def consecutive_success_or_pending_txn_count(singing_address_id, starting_nonce=0):

    expire_time = datetime.datetime.utcnow() - datetime.timedelta(
        seconds=current_app.config['PENDING_TRANSACTION_EXPIRY_SECONDS'])

    successful_or_pending = (BlockchainTransaction.query
                             .filter(BlockchainTransaction.signing_blockchain_address_id == singing_address_id)
                             # Success OR (Pending AND Newer than exp time)
                             .filter(or_(BlockchainTransaction.status == 'SUCCESS',
                                         and_(BlockchainTransaction.status == 'PENDING',
                                              BlockchainTransaction.created > expire_time)))
                             .filter(BlockchainTransaction.nonce >= starting_nonce)
                             .order_by(BlockchainTransaction.nonce.asc())
                             .all())


    nonce_set = set()

    for txn in successful_or_pending:
        nonce_set.add(txn.nonce)

    next_nonce = starting_nonce
    while next_nonce in nonce_set:
        next_nonce += 1

    # The while loop above overshot on its last loop
    return next_nonce

def get_usd_to_satoshi_rate():

    blockchain_task = celery_app.signature('worker.celery_tasks.get_usd_to_satoshi_rate')

    result = blockchain_task.apply_async()

    try:
        conversion_rate = result.wait(timeout=3, propagate=True, interval=0.5)

    except Exception as e:
        print(e)
        sentry.captureException()
        raise BlockchainError("Blockchain Error")

    finally:
        result.forget()

    return conversion_rate