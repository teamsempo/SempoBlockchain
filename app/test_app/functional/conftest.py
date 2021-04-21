import pytest
import os
import sys

from helpers.utils import will_func_test_blockchain
from helpers.mocks import MockBlockchainTasker, mock_class


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
            w3 = Web3(HTTPProvider(config.CHAINS['ETHEREUM']['HTTP_PROVIDER']))

            tx_hash = w3.eth.sendTransaction(
                {'to': address, 'from': w3.eth.accounts[0], 'value': 5 * 10 ** 18})
            hash = w3.eth.waitForTransactionReceipt(tx_hash)
            # print(f' Load account result {hash}')
            return hash
    return inner
