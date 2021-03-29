import pytest

from sql_persistence.interface import SQLPersistenceInterface
from sql_persistence.models import BlockchainTransaction, SynchronizedBlock
from eth_manager.blockchain_sync import blockchain_sync_constants
import datetime

class TestModels:
    # Generic filter parameters used a few times in the tests
    contract_address = '0x468F90c5a236130E5D51260A2A5Bfde834C694b6'
    contract_type = 'ERC20'
    filter_parameters = None
    filter_type = 'TRANSFER'
    decimals = 18
    block_epoch = 1

    # Resembles a w3 transaction object to the extent we need it to
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
    @pytest.mark.parametrize("block_epoch, expected_max_block", [
        (123, 123),
        ("latest", None),
        (None, None),
        (0, 0)
    ])
    def test_add_transaction_filter(self, blockchain_sync, persistence_module: SQLPersistenceInterface,
                                    block_epoch, expected_max_block):
        # Build filter
        blockchain_sync.add_transaction_filter(
            self.contract_address,
            self.contract_type,
            self.filter_parameters,
            self.filter_type,
            self.decimals,
            block_epoch
        )
        # Query the filter
        f = persistence_module.check_if_synchronization_filter_exists(self.contract_address, self.filter_parameters)
        # Validate the filter object
        assert f.contract_type == self.contract_type
        assert f.filter_parameters == self.filter_parameters
        assert f.filter_type == self.filter_type
        assert f.decimals == self.decimals
        assert f.max_block == expected_max_block

    # Tests get_blockchain_history
    def test_get_blockchain_transaction_history(self, mocker, blockchain_sync, processor, db_session):
        # Need a valid filter object since get_blockchain_transaction_history creates and modifies 
        # the SynchronizedBlock table, which has needs to be linked to a tx filter foreign key
        filter = blockchain_sync.add_transaction_filter(
            self.contract_address,
            self.contract_type,
            self.filter_parameters,
            self.filter_type,
            self.decimals,
            self.block_epoch
        )
        
        start_block = 1
        end_block = 500
        argument_filters = None
        filter_id = filter.id

        def dummy_contract(*args, **kwargs):
            class Contract():
                class events():
                    class Transfer():
                        def getLogs(**kwargs):
                            assert kwargs['fromBlock'] == start_block
                            assert kwargs['toBlock'] == end_block
                            assert kwargs['argument_filters'] == argument_filters
                            return []
            return Contract()
        mocker.patch.object(blockchain_sync.w3.eth, 'contract', dummy_contract)

        events = blockchain_sync.get_blockchain_transaction_history(self.contract_address, start_block, end_block, argument_filters, filter_id)

        for event in events:
            # Have to consume generator for test to halt
            assert event == None

        blocks = db_session.query(SynchronizedBlock).all()
        for b in blocks:
            assert b.status == 'SUCCESS'
        assert len(blocks) == 500
        
    def test_synchronize_third_party_transactions(
            self, mocker, blockchain_sync, processor, persistence_module: SQLPersistenceInterface
    ):
        # Create filters for this function to consume
        tf1_id = blockchain_sync.add_transaction_filter(
            self.contract_address,
            self.contract_type,
            self.filter_parameters,
            self.filter_type,
            self.decimals,
            self.block_epoch
        ).id

        tf2_id = blockchain_sync.add_transaction_filter(
            '0x000090c5a236130E5D51260A2A5Bfde834C694b6',
            self.contract_type,
            self.filter_parameters,
            self.filter_type,
            self.decimals,
            self.block_epoch
        ).id

        # Make get_latest_block_number return 12000, which will ensure we test the chunking every 5000 blocks
        mocker.patch.object(blockchain_sync, 'get_latest_block_number', lambda: 12000)

        ranges = []
        mocker.patch.object(blockchain_sync, 'process_chunk', lambda filter, floor, ceiling: ranges.append((filter.id, floor, ceiling)))
        blockchain_sync_constants.BLOCKS_PER_REQUEST=5000
        blockchain_sync.synchronize_third_party_transactions()
        assert ranges == [(1, 2, 5001), (1, 5002, 10001), (1, 10002, 12000), (2, 2, 5001), (2, 5002, 10001), (2, 10002, 12000)]

    def test_handle_event(self, mocker, blockchain_sync, processor, persistence_module: SQLPersistenceInterface):
        # Create dummy objects for this functions to consume (handle_event only uses decimals)
        class DummyFilter():
            decimals = 18
        filt = DummyFilter()

        class RequestsResp():
            ok = True

        # Check if handle_event halts (returns true) if there's already a synchronized transaction
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
        
        # If the webhook call doesn't work, it does not call mark_as_completed
        def check_correct_webhook_call_fail(transaction):
            assert transaction == tx
            resp = RequestsResp()
            resp.ok = False
            return resp

        # from celery_app import persistence_module as pm
        pm = persistence_module
        mocker.patch.object(blockchain_sync, 'call_webhook', check_correct_webhook_call_fail)
        mocker.patch.object(pm, 'get_transaction', lambda hash: tx)	
        mocker.patch.object(pm, 'create_external_transaction', lambda *args, **kwargs: tx)
        mark_as_completed_mock = mocker.patch.object(pm, 'mark_transaction_as_completed')

        result = blockchain_sync.handle_event(t, filt)
        assert result == True

        blockchain_sync.handle_event(t, filt)
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

        blockchain_sync.handle_event(t, filt)
        # Make sure mark_as_completed is called
        assert len(mark_as_completed_mock.call_args_list) == 1

    def test_get_metrics(self, mocker, blockchain_sync, processor, db_session, persistence_module: SQLPersistenceInterface):
        # Generate dummy activity for metrics
        tf1 = blockchain_sync.add_transaction_filter(
            '0x000090c5a236130E5D51260A2A5Bfde834C694b6',
            self.contract_type,
            self.filter_parameters,
            self.filter_type,
            self.decimals,
            self.block_epoch
        ).id

        tf2 = blockchain_sync.add_transaction_filter(
            '0x000090c5a236130E5D51260A2A5Bfde844C694b6',
            self.contract_type,
            self.filter_parameters,
            self.filter_type,
            self.decimals,
            self.block_epoch
        ).id

        success_tx = BlockchainTransaction(
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
        db_session.add(success_tx)

        fail_tx = BlockchainTransaction(
           _status = 'PENDING',
           block = 10,
           hash = '0x4444444444444444444444445',
           contract_address = self.contract_address,
           is_synchronized_with_app = True,
           recipient_address = '0x3333333333333333333333334',
           sender_address = '0x2222222222222222222222223',
           amount = 10,
           is_third_party_transaction = True
        )
        db_session.add(fail_tx)

        success_synchronized_block = SynchronizedBlock(
            block_number = 1,
            status = 'SUCCESS',
            is_synchronized = False,
            synchronization_filter_id = tf1,
            decimals = 18
        )
        db_session.add(success_synchronized_block)

        fail_synchronized_block = SynchronizedBlock(
            block_number = 2,
            status = 'FAILED',
            is_synchronized = False,
            synchronization_filter_id = tf1,
            decimals = 18
        )
        db_session.add(fail_synchronized_block)

        fail_synchronized_block2 = SynchronizedBlock(
            block_number = 3,
            status = 'FAILED',
            is_synchronized = False,
            synchronization_filter_id = tf1,
            decimals = 18
        )
        db_session.add(fail_synchronized_block2)
        
        fail_synchronized_block3 = SynchronizedBlock(
            block_number = 1,
            status = 'FAILED',
            is_synchronized = False,
            synchronization_filter_id = tf2,
            decimals = 18
        )
        db_session.add(fail_synchronized_block3)

        expected_resp = {
            'unsynchronized_transaction_count': {'0x468F90c5a236130E5D51260A2A5Bfde834C694b6': 1}, 
            'synchronized_transaction_count': {'0x468F90c5a236130E5D51260A2A5Bfde834C694b6': 1}, 
            'unsynchronized_block_count': {'0x000090c5a236130E5D51260A2A5Bfde834C694b6': 2, '0x000090c5a236130E5D51260A2A5Bfde844C694b6': 1}, 
            'synchronized_block_count': {'0x000090c5a236130E5D51260A2A5Bfde834C694b6': 1}, 
            'max_synchronized_blocks': {'0x000090c5a236130E5D51260A2A5Bfde834C694b6': 1, '0x000090c5a236130E5D51260A2A5Bfde844C694b6': 1}, 
            'last_time_synchronized': None
        }
        # Check base metrics
        resp = blockchain_sync.get_metrics()
        resp['last_time_synchronized'] = None
        assert resp == expected_resp

        # Check failed blocks
        failed_blocks = blockchain_sync.get_failed_block_fetches()
        expected_resp = {'0x000090c5a236130E5D51260A2A5Bfde834C694b6': [2, 3], '0x000090c5a236130E5D51260A2A5Bfde844C694b6': [1]}
        assert failed_blocks == expected_resp

        # Check failed callbacks
        failed_callbacks = blockchain_sync.get_failed_callbacks()
        expected_resp = {'0x468F90c5a236130E5D51260A2A5Bfde834C694b6': ['0x4444444444444444444444444']}
        assert failed_callbacks == expected_resp

    def test_force_fetch_block_range(self, mocker, blockchain_sync, processor, db_session, persistence_module: SQLPersistenceInterface):
        address = '0x000090c5a236130E5D51260A2A5Bfde834C694b6'
        f = blockchain_sync.add_transaction_filter(
            '0x000090c5a236130E5D51260A2A5Bfde834C694b6',
            self.contract_type,
            self.filter_parameters,
            self.filter_type,
            self.decimals,
            self.block_epoch
        )
        def check_input(filter, floor, ceiling):
            assert filter == f
            assert floor == 1
            assert ceiling == 20
        mocker.patch.object(blockchain_sync, 'process_chunk', check_input)
        blockchain_sync.force_fetch_block_range(address, 1, 20)

    def test_force_recall_webhook(self, mocker, blockchain_sync, processor, db_session, persistence_module: SQLPersistenceInterface):
        fail_tx = BlockchainTransaction(
           _status = 'PENDING',
           block = 10,
           hash = '0x4444444444444444444444445',
           contract_address = self.contract_address,
           is_synchronized_with_app = False,
           recipient_address = '0x3333333333333333333333334',
           sender_address = '0x2222222222222222222222223',
           amount = 10,
           is_third_party_transaction = True
        )
        db_session.add(fail_tx)

        class RequestsResp():
            ok = True
        assert fail_tx.is_synchronized_with_app == False
        def check_correct_webhook_call(transaction):
            assert transaction == fail_tx
            return RequestsResp()

        mocker.patch.object(blockchain_sync, 'call_webhook', check_correct_webhook_call)

        blockchain_sync.force_recall_webhook('0x4444444444444444444444445')

        assert fail_tx.is_synchronized_with_app == True
