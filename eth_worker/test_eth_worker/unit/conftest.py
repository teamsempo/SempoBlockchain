import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

import pytest
from sqlalchemy.orm import scoped_session
import redis
from web3 import Web3

import config
from eth_manager.processor import TransactionProcessor
from sql_persistence import engine, session_factory
from sql_persistence.interface import SQLPersistenceInterface
from sql_persistence.models import Base

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
    return SQLPersistenceInterface(
        red=None, session=db_session, first_block_hash='deadbeef01'
    )

@pytest.fixture(scope='function')
def processor(persistence_module, monkeypatch):
    w3 = Web3()
    
    monkeypatch.setattr(w3.eth, "sendRawTransaction", lambda x: None)
    monkeypatch.setattr(w3.eth, "sendRawTransaction", lambda x: None)

@pytest.fixture(scope='function')
def persistence_int(db_session):
    red = redis.Redis.from_url(config.REDIS_URL)

    return SQLPersistenceInterface(
        red=red, session=db_session, first_block_hash='deadbeef01'
    )
