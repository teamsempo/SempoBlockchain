import uuid
import pytest

from eth_keys import keys

from sql_persistence.interface import SQLPersistenceInterface
from sql_persistence.models import BlockchainWallet, BlockchainTask, BlockchainTransaction
from sempo_types import UUID

from eth_manager.blockchain_sync.blockchain_sync import add_transaction_filter, get_blockchain_transaction_history

class TestModels:
    # Generic filter parameters used a few times in the tests
    contract_address = '0x468F90c5a236130E5D51260A2A5Bfde834C694b6'
    contract_type = 'ERC20'
    filter_parameters = None
    filter_type = 'TRANSFER'
    decimals = 18
    block_epoch = None

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
    def test_get_blockchain_transaction_history(self, processor, mocker, persistence_module: SQLPersistenceInterface):
        # Need a valid filter object since get_blockchain_transaction_history creates and modifies 
        # the SynchronizedBlock table, which has needs to be linked to a tx filter foreign key
        filter = add_transaction_filter(self.contract_address, self.contract_type, self.filter_parameters, self.filter_type, self.decimals, self.block_epoch)
        
        start_block = 0 
        end_block = 500
        argument_filters = None
        filter_id = filter.id
        events = get_blockchain_transaction_history(self.contract_address, start_block, end_block, argument_filters, filter_id)
        for event in events:
            print(event)
        assert 1 == 1