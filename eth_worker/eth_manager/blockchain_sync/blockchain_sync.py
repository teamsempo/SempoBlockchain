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

import eth_manager.blockchain_sync.blockchain_sync_constants as sync_const
from eth_manager import red, w3, persistence_module
from eth_manager.ABIs import erc20_abi

# Hit the database to get the latest block number to which we're synced
def get_latest_block_number():
    return w3.eth.getBlock('latest').number

# Call webhook
def call_webhook(transaction):
    body = {
        'sender_blockchain_address': transaction.sender_address,
        'recipient_blockchain_address': transaction.recipient_address,
        'blockchain_transaction_hash': transaction.hash,
        'transfer_amount': float(transaction.amount)/(10**18), # Note: Tweak this later
        'contract_address': transaction.contract_address
    }
    r = requests.post(config.APP_HOST + '/api/v1/credit_transfer/internal/',
                      json=body,
                      auth=HTTPBasicAuth(config.INTERNAL_AUTH_USERNAME,
                                         config.INTERNAL_AUTH_PASSWORD)
                    )
    return r

# Get list of filters from redis
def synchronize_third_party_transactions():
    filters = persistence_module.get_all_filters()
    # Since the webook will timeout if we ask for too many blocks at once, we have to break 
    # the range we want into chunks.
    for f in filters:
        max_enqueued_block = f.max_block or 0
        max_enqueued_block = max_enqueued_block - 100000
        latest_block = get_latest_block_number()
        number_of_blocks_to_get = (latest_block - max_enqueued_block)

        # integer division, then add a chunk if there's a remainder
        number_of_chunks = int(number_of_blocks_to_get/sync_const.BLOCKS_PER_REQUEST) + (number_of_blocks_to_get % sync_const.BLOCKS_PER_REQUEST > 0)
        for chunk in range(number_of_chunks):
            floor = max_enqueued_block + (chunk * sync_const.BLOCKS_PER_REQUEST)
            ceiling = max_enqueued_block + ((chunk + 1) * sync_const.BLOCKS_PER_REQUEST)
            # filter_job objects are just filter objects with floors/ceilings set
            job = {
                'filter_id': f.id,
                'floor': floor,
                'ceiling': ceiling
            }
            red.rpush(sync_const.THIRD_PARTY_SYNC_JOBS, json.dumps(job))
        if ceiling:
            # Sometimes there won't be a ceiling, if there's no new chunks since the last time it ran
            persistence_module.set_filter_max_block(f.id, ceiling)
        # With the jobs set, we can now start processing them
        process_all_chunks()


# Iterates through all jobs made by synchronize_third_party_transactions
# Gets and processes them all!
def process_all_chunks():
    for filter_job in red.lrange(sync_const.THIRD_PARTY_SYNC_JOBS, 0, -1):
        task = json.loads(filter_job)
        filter = persistence_module.get_filter(task['filter_id'])
        transaction_history = get_blockchain_transaction_history(
            filter.contract_address, 
            task['floor'], 
            task['ceiling'], 
            filter.filter_parameters,
            filter.id
        )
        for transaction in transaction_history:
            handle_transaction(transaction)
        # Once a batch of chunks is completed, we can mark them completed
        persistence_module.set_block_range_status(task['floor'], task['ceiling'], 'SUCCESS')

# Processes newly found transaction event
# Creates database object for transaction
# Calls webhook
# Sets sync status (whether or not webhook was successful)
# Fallback if something goes wrong at this level: `is_synchronized_with_app` flag. Can batch unsynced stuff
def handle_transaction(transaction):
    # Check if transaction already exists (I.e. already synchronized, or first party transactions)
    transaction_object = persistence_module.get_transaction(hash=transaction.transactionHash.hex())
    if transaction_object and transaction_object.is_synchronized_with_app:
        return True
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
    print(transaction.transactionHash.hex())
    call_webhook(transaction_object)
    # Transactions which we fetched, but couldn't sync for whatever reason won't be marked as completed
    # in order to be retryable later
    persistence_module.mark_transaction_as_completed(transaction_object)
    # Only pop the list (delete job from queue) after success
    red.lpop(sync_const.THIRD_PARTY_SYNC_JOBS)


# Gets blockchain transaction history for given range
# Fallback if something goes wrong at this level: block-tracking table
def get_blockchain_transaction_history(contract_address, start_block, end_block = 'lastest', argument_filters = None, filter_id = None):
    # Creates DB objects for every block to monitor status
    print(f'Fetching block range {start_block} to {end_block}')

    persistence_module.add_block_range(start_block, end_block, filter_id)
    erc20_contract = w3.eth.contract(
        address = Web3.toChecksumAddress(contract_address),
        abi = erc20_abi.abi
    )
    try:
        filter = erc20_contract.events.Transfer.createFilter(
            fromBlock = start_block,
            toBlock = end_block,
            argument_filters = argument_filters
        )

        for event in filter.get_all_entries():
            yield event
    except:
        print(f'Failed fetching block range {start_block} to {end_block}')
        persistence_module.set_block_range_status(start_block, end_block, 'FAILED FETCHING BLOCKS')

# Adds transaction filter to database if it doesn't already exist
def add_transaction_filter(contract_address, contract_type, filter_parameters, filter_type):
    # See if there's already a filter with the same contract address AND type. If there is, do nothing
    # This lets you always add all filters at app-launch, without running an entire filter every time
    if not persistence_module.check_if_filter_exists(contract_address, contract_type):
        persistence_module.add_transaction_filter(contract_address, contract_type, filter_parameters, filter_type)
