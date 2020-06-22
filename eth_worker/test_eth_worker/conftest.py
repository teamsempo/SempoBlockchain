import os, sys
# Add config
source_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(source_path)

# Add src
source_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../eth_src"))
sys.path.append(source_path)

# Add helpers directory - pytest doesn't recommend packages in test dir
source_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "./helpers"))
sys.path.append(source_path)


import pytest
from sqlalchemy.orm import scoped_session
from web3 import Web3

import config
from eth_src.eth_manager.transaction_processor import TransactionProcessor
from eth_src.sql_persistence import engine, session_factory
from eth_src.sql_persistence.interface import SQLPersistenceInterface
from eth_src.sql_persistence.models import Base
from mocks import MockNonce, MockRedis, MockSendRawTxn

from utils import str_uuid

@pytest.fixture(scope='session', autouse=True)
def mock_queue_sig(mocker):
    def mock_response(sig, countdown):
        return str_uuid()

    print("Mocked!")

    mocker.patch('eth_src.celery_dispatchers.utils.queue_sig', mock_response)

@pytest.fixture(scope='function')
def db_session():
    # Create the database and the database table

    Base.metadata.create_all(engine)

    session = scoped_session(session_factory)

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope='function')
def persistence_module(db_session):
    red = MockRedis()

    return SQLPersistenceInterface(
        red=red, session=db_session, first_block_hash='deadbeef01'
    )

@pytest.fixture(scope='function')
def noncer():
    return MockNonce()

@pytest.fixture(scope='function')
def txn_sender():
    return MockSendRawTxn()

@pytest.fixture(scope='function')
def processor(persistence_module, noncer, monkeypatch):
    w3 = Web3()
    red = MockRedis()

    monkeypatch.setattr(w3.eth, "sendRawTransaction", lambda txn: True)
    monkeypatch.setattr(w3.eth, "getTransactionCount", noncer.get_transaction_count)
    monkeypatch.setattr(w3.eth, "estimateGas", lambda x: 40000)
    monkeypatch.setattr(w3.eth.account, "sign_transaction", lambda x: 40000)



    p = TransactionProcessor(
        ethereum_chain_id=1,
        w3=w3,
        red=red,
        gas_price_wei=100,
        gas_limit=400000,
        persistence_module=persistence_module
    )

    from eth_manager.contract_registry.ABIs import (
        erc20_abi,
    )

    p.registry.register_abi('ERC20', erc20_abi.abi)

    return p


@pytest.fixture(scope='function')
def dummy_wallet(db_session):
    from sql_persistence.models import BlockchainWallet

    w = BlockchainWallet()

    db_session.add(w)
    db_session.commit()

    return w


@pytest.fixture(scope='function')
def dummy_task(db_session, dummy_wallet):
    from sql_persistence.models import BlockchainTask

    task = BlockchainTask(
        uuid=str_uuid(),
        signing_wallet=dummy_wallet
    )

    db_session.add(task)
    db_session.commit()

    return task


@pytest.fixture(scope='function')
def dummy_transaction(db_session, dummy_task, dummy_wallet):
    from sql_persistence.models import BlockchainTransaction

    txn = BlockchainTransaction(
        signing_wallet=dummy_wallet
    )

    txn.task = dummy_task

    db_session.add(txn)
    db_session.commit()

    return txn

@pytest.fixture(scope='function')
def second_dummy_transaction(db_session, dummy_task, dummy_wallet):
    from sql_persistence.models import BlockchainTransaction

    txn = BlockchainTransaction(
        signing_wallet=dummy_wallet
    )

    txn.task = dummy_task

    db_session.add(txn)
    db_session.commit()

    return txn