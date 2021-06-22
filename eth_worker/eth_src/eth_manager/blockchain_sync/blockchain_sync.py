import json
from uuid import uuid4
import config
import requests
from requests.auth import HTTPBasicAuth
from math import ceil
from web3 import Web3

import eth_manager.blockchain_sync.blockchain_sync_constants as sync_const
from eth_manager.contract_registry.ABIs import erc20_abi


class BlockchainSyncer(object):

    # Hit the database to get the latest block number to which we're synced
    def get_latest_block_number(self):
        return self.w3.eth.getBlock('latest').number

    # Call app-level webhook with newfound transacitons
    def call_webhook(self, transaction):
        body = {
            'sender_blockchain_address': transaction.sender_address,
            'recipient_blockchain_address': transaction.recipient_address,
            'blockchain_transaction_hash': transaction.hash,
            'transfer_amount': int(transaction.amount or 0),
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
    def synchronize_third_party_transactions(self):
        filters = self.persistence.get_all_synchronization_filters()
        # Since the webook will timeout if we ask for too many blocks at once, we have to break
        # the range we want into chunks. Once all the chunk-jobs are formed and loaded into redis,
        # then trigger process_all_chunks, which will consume those jobs from redis
        total_blocks_retrieved = 0
        for f in filters:
            # Make sure a filter is only being executed once at a time
            have_lock = False
            lock = self.red.lock(f'third-party-sync-lock-{f.id}', timeout=sync_const.LOCK_TIMEOUT)
            try:
                have_lock = lock.acquire(blocking=False)
                if not have_lock:
                    config.logg.info(f'Skipping execution of synchronizing filter {f.id}, as it is already running in another process')
                    continue

                latest_block = self.get_latest_block_number()
                # If there's no filter.max_block (which is the default for auto-generated filters)
                # start tracking third party transactions by looking at the lastest_block
                max_fetched_block = f.max_block or latest_block
                number_of_blocks_to_get = (latest_block - max_fetched_block)
                number_of_chunks = ceil(number_of_blocks_to_get/sync_const.BLOCKS_PER_REQUEST)

                total_blocks_retrieved += number_of_blocks_to_get

                for chunk in range(number_of_chunks):
                    floor = max_fetched_block + (chunk * sync_const.BLOCKS_PER_REQUEST) + 1
                    ceiling = max_fetched_block + ((chunk + 1) * sync_const.BLOCKS_PER_REQUEST)
                    if ceiling > latest_block:
                        ceiling = latest_block
                    self.process_chunk(f, floor, ceiling)
                    self.persistence.set_filter_max_block(f.id, ceiling)
                    lock.reacquire()

                if number_of_chunks == 0:
                    self.persistence.set_filter_max_block(f.id, latest_block)
            finally:
                if have_lock:
                    lock.release()
        return total_blocks_retrieved

    # Gets history for given range, and runs handle_event on all of them
    # This is the second stage in the third party transaction processing pipeline!
    def process_chunk(self, filter, floor, ceiling):
        transaction_history = self.get_blockchain_transaction_history(
                filter.contract_address,
                floor,
                ceiling,
                filter.filter_parameters,
                filter.id
            )
        for event in transaction_history:
            self.handle_event(event, filter)
        return 'Success'

    # Processes newly found transaction event
    # Creates database object for transaction
    # Calls webhook
    # Sets sync status (whether or not webhook was successful)
    def handle_event(self, transaction, filter):
        transaction_object = self.persistence.get_transaction(hash=transaction.transactionHash.hex())
        # If transaction doesn't exist, make it. Even if it does exist, and it's synchronized via first-party sync
        # we still want to send it with third-party (here) as insurance that tx sync is running correctly.
        if not transaction_object:
            transaction_object = self.persistence.create_external_transaction(
                status = 'SUCCESS',
                block = transaction.blockNumber,
                hash = str(transaction.transactionHash.hex()),
                contract_address = transaction.address,
                is_synchronized_with_app = False,
                recipient_address = transaction.args['to'],
                sender_address = transaction.args['from'],
                amount = float(transaction.args['value'])/(10**filter.decimals)*100 #To cents
            )

        webook_resp = self.call_webhook(transaction_object)
        # Transactions which we fetched, but couldn't sync for whatever reason won't be marked as completed
        # in order to be retryable later
        if webook_resp.ok:
            self.persistence.mark_transaction_as_completed(transaction_object)
        return True

    # Gets blockchain transaction history for given range
    # Fallback if something goes wrong at this level: block-tracking table
    def get_blockchain_transaction_history(self, contract_address, start_block, end_block = 'lastest', argument_filters = None, filter_id = None):
        # Creates DB objects for every block to monitor status
        config.logg.info(f'Fetching block range {start_block} to {end_block} for contract {contract_address}')

        self.persistence.add_block_range(start_block, end_block, filter_id)
        erc20_contract = self.w3.eth.contract(
            address = Web3.toChecksumAddress(contract_address),
            abi = erc20_abi.abi
        )
        try:
            events = erc20_contract.events.Transfer.getLogs(
                fromBlock = start_block,
                toBlock = end_block,
                argument_filters = argument_filters
            )
            for event in events:
                yield event
            # Once a batch of chunks is completed, we can mark them completed
            self.persistence.set_block_range_status(start_block, end_block, 'SUCCESS', filter_id)

        except:
            # Setting block status as a range since individual blocks can't fail at this stage (as we are getting a range of blocks)
            self.persistence.set_block_range_status(start_block, end_block, 'FAILED', filter_id)
            raise Exception(f'Failed fetching block range {start_block} to {end_block} for contract {contract_address}')

    # Adds transaction filter to database if it doesn't already exist
    def add_transaction_filter(self, contract_address, contract_type, filter_parameters, filter_type, decimals = 18, block_epoch=None):
        # See if there's already a filter with the same contract address AND type. If there is, do nothing
        # This lets you always add all filters at app-launch, without running an entire filter every time
        if not contract_address:
            raise Exception('No contract_address found for new contract filter')
        # Block epoch being None is a sentinel for `latest`
        if block_epoch == 'latest' or block_epoch is None:
            epoch = None
        else:
            epoch = int(block_epoch)
        if not self.persistence.check_if_synchronization_filter_exists(contract_address, filter_parameters):
            # Set max_block to block_epoch to act as a de-factor zero-point
            config.logg.info(f'No filter found for address {contract_address} with parameters {filter_parameters}. Creating.')
            return self.persistence.add_transaction_filter(
                contract_address,
                contract_type,
                filter_parameters,
                filter_type, decimals,
                block_epoch=epoch
            )

    def get_metrics(self):
        return self.persistence.get_transaction_sync_metrics()

    def get_failed_block_fetches(self):
        return self.persistence.get_failed_block_fetches()

    def get_failed_callbacks(self):
        return self.persistence.get_failed_callbacks()

    def force_fetch_block_range(self, filter_address, floor, ceiling):
        filter = self.persistence.get_synchronization_filter_by_address(filter_address)
        if not filter:
            raise Exception(f'{filter_address} does not have an active transaction sync filter')
        return self.process_chunk(filter, floor, ceiling)

    def force_recall_webhook(self, transaction_hash):
        transaction = self.persistence.get_transaction_by_hash(transaction_hash)
        if transaction:
            webook_resp = self.call_webhook(transaction)
            # Transactions which we fetched, but couldn't sync for whatever reason won't be marked as completed
            # in order to be retryable later
            if webook_resp.ok:
                self.persistence.mark_transaction_as_completed(transaction)
                return 'Success'
            else:
                raise Exception(f'Force recall webook failed for {transaction_hash}')
        else:
            return f'Transaction {transaction_hash} not found!'

    def __init__(self, w3, red, persistence):
        self.w3 = w3
        self.red = red
        self.persistence = persistence
