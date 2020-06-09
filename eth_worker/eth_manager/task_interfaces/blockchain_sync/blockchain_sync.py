import json
from uuid import uuid4
import config
import requests
from requests.auth import HTTPBasicAuth

from web3 import (
    Web3,
    WebsocketProvider,
    HTTPProvider
)
from sql_persistence.models import BlockchainTransaction, BlockchainTask
import eth_manager.task_interfaces.blockchain_sync.blockchain_sync_constants as sync_const
from eth_manager import red, w3, persistence_module

# Hit the database to get the latest block number to which we're synced
def get_latest_block_number():
    return w3.eth.getBlock('latest').number

# Call webhook
def call_webhook(transaction):
    body = {
        'sender_blockchain_address': transaction.sender_address,
        'recipient_blockchain_address': transaction.recipient_address,
        'blockchain_transaction_hash': transaction.hash,
        'transfer_amount': float(transaction.amount), # Change this type later
        'contract_address': transaction.contract_address
    }
    r = requests.post(config.APP_HOST + '/api/v1/credit_transfer/internal/',
                      json=body,
                      auth=HTTPBasicAuth(config.INTERNAL_AUTH_USERNAME,
                                         config.INTERNAL_AUTH_PASSWORD)
                    )
    return r

def synchronize_third_party_transactions():
    # Get list of filters from redis
    filters = json.loads(red.get(sync_const.THIRD_PARTY_SYNC_FILTERS))
    # Since the webook will timeout if we ask for too many blocks at once, we have to break 
    # the range we want into chunks.
    for f in filters:
        # We prioritize MAX_ENQUEUED_BLOCK because a block could be enqueued on the worker-side
        # which the app doesn't know about
        max_enqueued_block = int(red.get(sync_const.MAX_ENQUEUED_BLOCK % str(f['id'])) or f['last_block_synchronized'])
        max_enqueued_block = int(red.get(sync_const.MAX_ENQUEUED_BLOCK % str(f['id'])) or f['last_block_synchronized'])
        latest_block = get_latest_block_number()
        number_of_chunks_to_get = (latest_block - max_enqueued_block)

        # integer division, then add a chunk if there's a remainder
        number_of_chunks = int(number_of_chunks_to_get/sync_const.BLOCKS_PER_REQUEST) + (number_of_chunks_to_get % sync_const.BLOCKS_PER_REQUEST > 0)
        for chunk in range(number_of_chunks):
            floor = max_enqueued_block + (chunk * sync_const.BLOCKS_PER_REQUEST)
            ceiling = max_enqueued_block + ((chunk + 1) * sync_const.BLOCKS_PER_REQUEST)
            # filter_job objects are just filter objects with floors/ceilings set
            f['floor'] = floor
            f['ceiling'] = ceiling
            red.rpush(sync_const.THIRD_PARTY_SYNC_JOBS, json.dumps(f))
            red.set(sync_const.MAX_ENQUEUED_BLOCK % str(f['id']), ceiling)
        # With the jobs set, we can now start processing them
        process_all_chunks()

# Iterates through all jobs made by synchronize_third_party_transactions
# Gets and processes them all!
def process_all_chunks():
    for filter_job in red.lrange(sync_const.THIRD_PARTY_SYNC_JOBS, 0, -1):
        filter_job = json.loads(filter_job)
        transaction_history = get_blockchain_transaction_history(
            filter_job['contract_address'], 
            filter_job['floor'], 
            filter_job['ceiling'], 
            filter_job['filter_parameters']
        )
        for transaction in transaction_history:
            handle_transaction(transaction)

# Processes newly found transaction event
# Creates database object for transaction
# Calls webhook
# Sets sync status (whether or not webhook was successful)
# Fallback if something goes wrong at this level: `is_synchronized_with_app` flag. Can batch unsynced stuff
def handle_transaction(transaction):
    transaction_object = persistence_module.create_external_transaction(
        status = 'SUCCESS',
        block = transaction.blockNumber,
        hash = str(transaction.transactionHash.hex()),
        contract_address = transaction.address,
        is_synchronized_with_app = False,
        recipient_address = transaction.args['to'],
        sender_address = transaction.args['from'],
        amount = transaction.args['value']
    )

    call_webhook(transaction_object)
    # Transactions which we fetched, but couldn't sync for whatever reason won't be marked as completed
    # in order to be retryable later
    persistence_module.mark_transaction_as_completed(transaction_object)
    # Only pop the list (delete job from queue) after success
    red.lpop(sync_const.THIRD_PARTY_SYNC_JOBS)


# Gets blockchain transaction history for given range
# Fallback if something goes wrong at this level: block-tracking table
def get_blockchain_transaction_history(contract_address, start_block, end_block = 'lastest', argument_filters = None):
    erc20_contract = w3.eth.contract(
        address = Web3.toChecksumAddress(contract_address),
        abi = sync_const.ERC20_ABI
    )

    filter = erc20_contract.events.Transfer.createFilter(
        fromBlock = start_block,
        toBlock = end_block,
        argument_filters = argument_filters
    )

    for event in filter.get_all_entries():
        yield event
    pass
