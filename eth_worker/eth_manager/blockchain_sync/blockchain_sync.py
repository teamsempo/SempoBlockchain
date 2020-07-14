import json
from uuid import uuid4
import config
import requests
from requests.auth import HTTPBasicAuth
from math import ceil
from web3 import Web3

import eth_manager.blockchain_sync.blockchain_sync_constants as sync_const
from eth_manager import red, w3_websocket, persistence_module
from eth_manager.ABIs import erc20_abi

# Hit the database to get the latest block number to which we're synced
def get_latest_block_number():
    print('getting latest block number')
    return w3_websocket.eth.getBlock('latest').number

# Call app-level webhook with newfound transacitons
def call_webhook(transaction):
    body = {
        'sender_blockchain_address': transaction.sender_address,
        'recipient_blockchain_address': transaction.recipient_address,
        'blockchain_transaction_hash': transaction.hash,
        'transfer_amount': int(transaction.amount),
        'contract_address': transaction.contract_address
    }
    r = requests.post(config.APP_HOST + '/api/v1/credit_transfer/internal/',
                        json=body,
                        auth=HTTPBasicAuth(config.INTERNAL_AUTH_USERNAME,
                                        config.INTERNAL_AUTH_PASSWORD),
                        timeout=30
                    )
    return r

# Get list of filters from redis. This is the starting point of the synchronization process
def synchronize_third_party_transactions():
    print('STARTING SYNC')
    filters = persistence_module.get_all_synchronization_filters()
    # Since the webook will timeout if we ask for too many blocks at once, we have to break 
    # the range we want into chunks. Once all the chunk-jobs are formed and loaded into redis,
    # then trigger process_all_chunks, which will consume those jobs from redis
    for f in filters:
        # Make sure a filter is only being executed once at a time
        have_lock = False
        lock = red.lock(f'third-party-sync-lock-{f.id}', timeout=sync_const.LOCK_TIMEOUT)
        have_lock = lock.acquire(blocking=False)
        if not have_lock:
            config.logg.info(f'Skipping execution of synchronizing filter {f.id}, as it is already running in another process')
            continue
        print('STARTING TO GET LATEST BLOCK')
        latest_block = get_latest_block_number()
        config.logg.info('LATEST BLOCK')
        config.logg.info(latest_block)
        # If there's no filter.max_block (which is the default for auto-generated filters)
        # start tracking third party transactions by looking at the lastest_block
        max_fetched_block = f.max_block or latest_block
        config.logg.info('max_fetched_block')
        config.logg.info(max_fetched_block)
        number_of_blocks_to_get = (latest_block - max_fetched_block)
        config.logg.info('number_of_blocks_to_get')
        config.logg.info(number_of_blocks_to_get)
        number_of_chunks = ceil(number_of_blocks_to_get/sync_const.BLOCKS_PER_REQUEST)
        config.logg.info('number_of_chunks')
        config.logg.info(number_of_chunks)
        for chunk in range(number_of_chunks):
            config.logg.info('chunk')
            config.logg.info(chunk)
            floor = max_fetched_block + (chunk * sync_const.BLOCKS_PER_REQUEST) + 1
            ceiling = max_fetched_block + ((chunk + 1) * sync_const.BLOCKS_PER_REQUEST)
            if ceiling > latest_block:
                ceiling = latest_block
            process_chunk(f, floor, ceiling)
            persistence_module.set_filter_max_block(f.id, ceiling)
            lock.reacquire()

        if number_of_chunks == 0:
            persistence_module.set_filter_max_block(f.id, latest_block)
        if have_lock:
            lock.release()
    return True

# Gets history for given range, and runs handle_transaction on all of them
# This is the second stage in the third party transaction processing pipeline!
def process_chunk(filter, floor, ceiling):
    config.logg.info('proc_chunk')
    config.logg.info(filter)
    config.logg.info(floor)
    config.logg.info(ceiling)
    transaction_history = get_blockchain_transaction_history(
            filter.contract_address, 
            floor, 
            ceiling, 
            filter.filter_parameters,
            filter.id
        )
    for transaction in transaction_history:
        config.logg.info('LoopTX')
        config.logg.info(transaction)
        handle_transaction(transaction, filter)

# Processes newly found transaction event
# Creates database object for transaction
# Calls webhook
# Sets sync status (whether or not webhook was successful)
# Fallback if something goes wrong at this level: `is_synchronized_with_app` flag. Can batch unsynced stuff
def handle_transaction(transaction, filter):
    # Check if transaction already exists (I.e. already synchronized, or first party transactions)
    transaction_object = persistence_module.get_transaction(hash=transaction.transactionHash.hex())
    if transaction_object and transaction_object.is_synchronized_with_app:
        return True
    if not transaction_object:
        transaction_object = persistence_module.create_external_transaction(
            status = 'SUCCESS',
            block = transaction.blockNumber,
            hash = str(transaction.transactionHash.hex()),
            contract_address = transaction.address,
            is_synchronized_with_app = False,
            recipient_address = transaction.args['to'],
            sender_address = transaction.args['from'],
            amount = float(transaction.args['value'])/(10**filter.decimals)
        )

    webook_resp = call_webhook(transaction_object)
    # Transactions which we fetched, but couldn't sync for whatever reason won't be marked as completed
    # in order to be retryable later
    if webook_resp.ok:
        persistence_module.mark_transaction_as_completed(transaction_object)
    return True

# Gets blockchain transaction history for given range
# Fallback if something goes wrong at this level: block-tracking table
def get_blockchain_transaction_history(contract_address, start_block, end_block = 'lastest', argument_filters = None, filter_id = None):
    # Creates DB objects for every block to monitor status
    config.logg.info(f'Fetching block range {start_block} to {end_block} for contract {contract_address}')

    persistence_module.add_block_range(start_block, end_block, filter_id)
    erc20_contract = w3_websocket.eth.contract(
        address = Web3.toChecksumAddress(contract_address),
        abi = erc20_abi.abi
    )
    print('contract_address')
    print(contract_address)
    print('start_block')
    print(start_block)
    print('end_block')
    print(end_block)
    print('argument_filters')
    print(argument_filters)
    print('filter_id')
    print(filter_id)
    print('Start making filter')
    try:
        filter = erc20_contract.events.Transfer.createFilter(
            fromBlock = start_block,
            toBlock = end_block,
            argument_filters = argument_filters
        )
        print('FILTER')
        print(filter)
        for event in filter.get_all_entries():
            print('------EVENT-------')
            print('------EVENT-------')
            print('------EVENT-------')
            print(event)
            yield event
        print('done')
        # Once a batch of chunks is completed, we can mark them completed
        persistence_module.set_block_range_status(start_block, end_block, 'SUCCESS', filter_id)

    except:
        # Setting block status as a range since individual blocks can't fail at this stage (as we are getting a range of blocks)
        persistence_module.set_block_range_status(start_block, end_block, 'FAILED', filter_id)
        raise Exception(f'Failed fetching block range {start_block} to {end_block} for contract {contract_address}')

# Adds transaction filter to database if it doesn't already exist
def add_transaction_filter(contract_address, contract_type, filter_parameters, filter_type, decimals = 18, block_epoch=None):
    # See if there's already a filter with the same contract address AND type. If there is, do nothing
    # This lets you always add all filters at app-launch, without running an entire filter every time
    if not contract_address:
        raise Exception('No contract_address found for new contract filter')
    if not persistence_module.check_if_synchronization_filter_exists(contract_address, filter_parameters):
        # Set max_block to block_epoch to act as a de-factor zero-point
        config.logg.info(f'No filter found for address {contract_address} with parameters {filter_parameters}. Creating.')
        return persistence_module.add_transaction_filter(contract_address, contract_type, filter_parameters, filter_type, decimals, block_epoch=block_epoch)
