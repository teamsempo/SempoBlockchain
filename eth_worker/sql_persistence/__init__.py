from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool

import config

engine = create_engine(
    config.ETH_DATABASE_URI,
    poolclass=NullPool,
    connect_args={'connect_timeout': 5},
    pool_pre_ping=True,
    echo=False,
    echo_pool=False,
)
session_factory = sessionmaker(autocommit=False, autoflush=True, bind=engine)
session = scoped_session(session_factory)