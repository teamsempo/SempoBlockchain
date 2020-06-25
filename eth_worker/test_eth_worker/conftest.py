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
import redis
from web3 import Web3

import config
from eth_src.eth_manager.transaction_processor import TransactionProcessor
from eth_src.sql_persistence import engine, session_factory
from eth_src.sql_persistence.interface import SQLPersistenceInterface
from eth_src.sql_persistence.models import Base
from mocks import MockNonce, MockRedis, MockSendRawTxn

from utils import str_uuid


@pytest.fixture(autouse=True)
def mock_queue_sig(monkeypatch):
    def mock_response(sig, countdown):
        return str_uuid()

    import celery_dispatchers.utils
    monkeypatch.setattr(celery_dispatchers.utils, 'queue_sig', mock_response)

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
def mock_txn_send():
    return MockSendRawTxn()

@pytest.fixture()
def mock_w3(monkeypatch, noncer, mock_txn_send):
    w3 = Web3()

    def txn_signer(transaction_dict, private_key):
        from eth_account.datastructures import AttributeDict
        from hexbytes import (
            HexBytes
        )

        return AttributeDict({
            # Allows us to snoop on the txn data without dealing with hard-to-reason-with encoded data
            'rawTransaction': transaction_dict,
            'hash':  HexBytes(b'0xdeadbeef1'),
            'r': 1,
            's': 2,
            'v': 3,
        })

    monkeypatch.setattr(w3.eth, "getTransactionCount", noncer.get_transaction_count)
    monkeypatch.setattr(w3.eth, "estimateGas", lambda x: 40000)
    monkeypatch.setattr(w3.eth.account, "sign_transaction", txn_signer)
    monkeypatch.setattr(w3.eth, "sendRawTransaction", lambda x: mock_txn_send.send(x))


    return w3

@pytest.fixture(scope='function')
def processor(persistence_module, mock_w3):

    p = TransactionProcessor(
        ethereum_chain_id=1,
        w3=mock_w3,
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