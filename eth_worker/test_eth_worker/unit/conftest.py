import pytest
from sqlalchemy.orm import scoped_session
import redis

import config
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
def persistence_int(db_session):
    red = redis.Redis.from_url(config.REDIS_URL)

    return SQLPersistenceInterface(
        red=red, session=db_session, first_block_hash='deadbeef01'
    )