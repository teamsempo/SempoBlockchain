import pytest
import os
import sys
app_dir = os.path.abspath(os.path.join(os.getcwd(), "app"))
sys.path.append(app_dir)
sys.path.append(os.getcwd())


@pytest.fixture(scope='module')
def load_account():
    from web3 import (
        Web3,
        HTTPProvider
    )
    import config

    def inner(address):
        w3 = Web3(HTTPProvider(config.ETH_HTTP_PROVIDER))

        tx_hash = w3.eth.sendTransaction(
            {'to': address, 'from': w3.eth.accounts[0], 'value': 5 * 10 ** 18})
        return w3.eth.waitForTransactionReceipt(tx_hash)

    return inner