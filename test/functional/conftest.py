import pytest
from helpers.utils import mock_class, will_func_test_blockchain
from helpers.blockchain_tasker import MockBlockchainTasker
from migrations.seed import create_ussd_menus, create_business_categories

@pytest.fixture(scope='module', autouse=True)
def mock_blockchain_tasks(monkeymodule):
    from server import bt
    if will_func_test_blockchain():
        print('~~~NOT Mocking Blockchain Endpoints, Eth Worker will be tested~~~')
    else:
        print('~~~Mocking Blockchain Endpoints, Eth Worker will NOT be tested~~~')
        mock_class(bt, MockBlockchainTasker, monkeymodule)

@pytest.fixture(scope='module')
def load_account():
    from web3 import (
        Web3,
        HTTPProvider
    )
    import config

    def inner(address):
        if will_func_test_blockchain():
            w3 = Web3(HTTPProvider(config.ETH_HTTP_PROVIDER))

            tx_hash = w3.eth.sendTransaction(
                {'to': address, 'from': w3.eth.accounts[0], 'value': 5 * 10 ** 18})
            hash = w3.eth.waitForTransactionReceipt(tx_hash)
            # print(f' Load account result {hash}')
            return hash
    return inner

@pytest.fixture(scope='module')
def init_seed(test_client, init_database):
    create_ussd_menus()
    create_business_categories()
