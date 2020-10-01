import pytest
from faker.providers import phone_number
from faker import Faker

from server import create_app, db

from helpers.mocks import MockMiscTasker, MockBlockchainTasker, MockUssdTasker, mock_class

fake = Faker()
fake.add_provider(phone_number)

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


# Function scoped fixtures

@pytest.fixture(scope='function')
def create_transfer_account(init_database, create_master_organisation):
    from server.models.transfer_account import TransferAccount
    transfer_account = TransferAccount()

    init_database.session.add(transfer_account)
    init_database.session.commit()
    return transfer_account

@pytest.fixture(scope='function')
def create_transfer_account_user(init_database, create_organisation):
    from server.utils.user import create_transfer_account_user
    user = create_transfer_account_user(first_name='Transfer',
                                        last_name='User',
                                        phone=fake.msisdn(),
                                        organisation=create_organisation)
    init_database.session.commit()
    return user

create_transfer_account_user_2 = create_transfer_account_user

@pytest.fixture(scope='function')
def create_user_with_existing_transfer_account(test_client, init_database, create_transfer_account):
    from server.utils.user import create_transfer_account_user
    user = create_transfer_account_user(first_name='Existing Transfer', last_name='User',
                                        phone=fake.msisdn(),
                                        existing_transfer_account=create_transfer_account)
    db.session.commit()
    return user
