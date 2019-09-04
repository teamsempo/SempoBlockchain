from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON

import datetime

engine = create_engine('sqlite:///database.db', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

class ModelBase(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class BlockchainTask(ModelBase):
    __tablename__ = 'blockchain_task'

    signing_address = Column(String)

    function = Column(String)
    args = Column(JSON)
    kwargs = Column(JSON)

    transactions = relationship('BlockchainTransaction',
                                backref='blockchain_task',
                                lazy='dynamic',
                                foreign_keys='BlockchainTransaction.blockchain_task_id')


class BlockchainTransaction(ModelBase):
    __tablename__ = 'blockchain_transaction'

    signing_address = Column(String)

    status = Column(String)  # PENDING, SUCCESS, FAILED
    message = Column(String)
    block = Column(Integer)
    submitted_date = Column(DateTime)
    mined_date = Column(DateTime)
    hash = Column(String)
    nonce = Column(Integer)

    blockchain_task_id = Column(Integer, ForeignKey(BlockchainTask.id))
