import pytest

from helpers.mocks import MockMiscTasker, MockBlockchainTasker, MockUssdTasker, mock_class


@pytest.fixture(scope='module')
def load_account():
    """
    Allows us to unit test without spooling up a test blockchain network
    """
    def inner(address):
        pass

    return inner


@pytest.fixture(scope='module', autouse=True)
def mock_ussd_tasks(monkeymodule):
    from server import ussd_tasker
    mock_class(ussd_tasker, MockUssdTasker, monkeymodule)


@pytest.fixture(scope='module', autouse=True)
def mock_blockchain_tasks(monkeymodule):
    from server import bt
    mock_class(bt, MockBlockchainTasker, monkeymodule)


@pytest.fixture(scope='module', autouse=True)
def mock_misc_tasks(monkeymodule):
    from server import mt
    mock_class(mt, MockMiscTasker, monkeymodule)