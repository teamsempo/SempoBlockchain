import uuid
import pytest

from eth_keys import keys

from sql_persistence.interface import SQLPersistenceInterface
from sql_persistence.models import BlockchainWallet, BlockchainTask, BlockchainTransaction
from sempo_types import UUID

from eth_manager.ABIs import erc20_abi
from eth_manager.blockchain_sync.blockchain_sync import add_transaction_filter, get_blockchain_transaction_history, synchronize_third_party_transactions, handle_transaction
from eth_manager.blockchain_sync import blockchain_sync
from sql_persistence.models import BlockchainTransaction

class TestModels:
    # Generic filter parameters used a few times in the tests
    contract_address = '0x468F90c5a236130E5D51260A2A5Bfde834C694b6'
    contract_type = 'ERC20'
    filter_parameters = None
    filter_type = 'TRANSFER'
    decimals = 18
    block_epoch = None
    
    # Resembles a w3 transaction object to the extend we need it to
    class Transaction():
        class Hash():
            hash = None
            def hex(self):
                return self.hash
            def __init__(self, hash):
                self.hash=hash
    
        blockNumber = 1
        transactionHash = Hash(5)
        address = ''
        is_synchronized_with_app = False
        args = {
            'to': '',
            'from': '',
            'value': 0
        }
        def __init__(self, block_number, hash, address, is_synchronized_with_app, to, fr, value):
            self.block_number = block_number
            self.transactionHash = self.Hash(hash)
            self.address = address
            self.is_synchronized_with_app = is_synchronized_with_app
            self.args = {
                'to': to,
                'from': fr,
                'value': value
            }
    
    # Checks that add_transaction_filter correctly generates transaction_filter objects
    # and inserts them
    def test_add_transaction_filter(self, persistence_module: SQLPersistenceInterface):
        # Build filter
        add_transaction_filter(self.contract_address, self.contract_type, self.filter_parameters, self.filter_type, self.decimals, self.block_epoch)
        # Query the filter
        f = persistence_module.check_if_synchronization_filter_exists(self.contract_address, self.filter_parameters)
        # Validate the filter object
        assert f.contract_type == self.contract_type
        assert f.filter_parameters == self.filter_parameters
        assert f.filter_type == self.filter_type
        assert f.decimals == self.decimals
        assert f.max_block == self.block_epoch

    # Tests get_blockchain_history
    def test_get_blockchain_transaction_history(self, mocker, processor):
        # Need a valid filter object since get_blockchain_transaction_history creates and modifies 
        # the SynchronizedBlock table, which has needs to be linked to a tx filter foreign key
        filter = add_transaction_filter(self.contract_address, self.contract_type, self.filter_parameters, self.filter_type, self.decimals, self.block_epoch)
        
        start_block = 0 
        end_block = 500
        argument_filters = None
        filter_id = filter.id

        def dummy_contract(*args, **kwargs):
            class Filter():
                def get_all_entries(self):
                    yield None
            class Contract():
                class events():
                    class Transfer():
                        def createFilter(**kwargs):
                            assert kwargs['fromBlock'] == start_block
                            assert kwargs['toBlock'] == end_block
                            assert kwargs['argument_filters'] == argument_filters
                            return Filter()
            return Contract()
        from eth_manager import w3_websocket
        mocker.patch.object(w3_websocket.eth, 'contract', dummy_contract)

        events = get_blockchain_transaction_history(self.contract_address, start_block, end_block, argument_filters, filter_id)

        for event in events:
            # Have to consume generator for test to halt
            assert event == None

    def test_synchronize_third_party_transactions(self, mocker, processor, persistence_module: SQLPersistenceInterface):
        # Create filters for this function to consume
        tf1_id = add_transaction_filter(self.contract_address, self.contract_type, self.filter_parameters, self.filter_type, self.decimals, self.block_epoch).id
        tf2_id = add_transaction_filter('0x000090c5a236130E5D51260A2A5Bfde834C694b6', self.contract_type, self.filter_parameters, self.filter_type, self.decimals, self.block_epoch).id
        # Make get_latest_block_number return 12000, which will ensure we test the chunking every 5000 blocks
        mocker.patch.object(blockchain_sync, 'get_latest_block_number', lambda: 12000)

        ranges = []
        mocker.patch.object(blockchain_sync, 'process_chunk', lambda filter, floor, ceiling: ranges.append((filter.id, floor, ceiling)))
        
        synchronize_third_party_transactions()
        assert ranges == [(tf1_id, 1, 5000), (tf1_id, 5001, 10000), (tf1_id, 10001, 12000), (tf2_id, 1, 5000), (tf2_id, 5001, 10000), (tf2_id, 10001, 12000)]

    def test_handle_transaction(self, mocker, processor, persistence_module: SQLPersistenceInterface):
        # Create dummy objects for this functions to consume (handle_transaction only uses decimals)
        class DummyFilter():
            decimals = 18
        filt = DummyFilter()

        class RequestsResp():
            ok = True

        # Check if handle_transaction halts (returns true) if there's already a synchronized transaction 
        # with the same ID in the DB
        t = self.Transaction(
            10, 
            '0x1111111111111111111111111111', 
            self.contract_address, 
            True, 
            '0x2222222222222222222222222', 
            '0x3333333333333333333333333', 
            10
        )
        from eth_manager import persistence_module as pm
        mocker.patch.object(pm, 'get_transaction', lambda hash: t)
        mocker.patch.object(pm, 'create_external_transaction', lambda *args, **kwargs: tx)
        mark_as_completed_mock = mocker.patch.object(pm, 'mark_transaction_as_completed')

        result = handle_transaction(t, filt)
        assert result == True


        # If the webhook call doesn't work, it does not call mark_as_completed
        tx = BlockchainTransaction(
           _status = 'PENDING',
           block = 10,
           hash = '0x5555555555555555555555555',
           contract_address = self.contract_address,
           is_synchronized_with_app = False,
           recipient_address = '0x3333333333333333333333333',
           sender_address = '0x2222222222222222222222222',
           amount = 10,
           is_third_party_transaction = True
        )
        def check_correct_webhook_call_fail(transaction):
            assert transaction == tx
            resp = RequestsResp()
            resp.ok = False
            return resp
        mocker.patch.object(blockchain_sync, 'call_webhook', check_correct_webhook_call_fail)
        handle_transaction(t, filt)
        # Make sure mark_as_completed is NOT called
        assert len(mark_as_completed_mock.call_args_list) == 0


        # If the filter isn't already synchronized, create the object and call the webhook
        mocker.patch.object(pm, 'get_transaction', lambda hash: None)
        tx = BlockchainTransaction(
           _status = 'PENDING',
           block = 10,
           hash = '0x4444444444444444444444444',
           contract_address = self.contract_address,
           is_synchronized_with_app = False,
           recipient_address = '0x3333333333333333333333333',
           sender_address = '0x2222222222222222222222222',
           amount = 10,
           is_third_party_transaction = True
        )
        # Make sure call_webhook is called with the right data
        def check_correct_webhook_call(transaction):
            assert transaction == tx
            return RequestsResp()
        mocker.patch.object(blockchain_sync, 'call_webhook', check_correct_webhook_call)
        
        handle_transaction(t, filt)
        # Make sure mark_as_completed is called
        assert len(mark_as_completed_mock.call_args_list) == 1

