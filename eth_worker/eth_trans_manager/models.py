from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import scoped_session
from sqlalchemy import select, func, case
import datetime

import config

STATUS_STRING_TO_INT = {'SUCCESS': 1, 'PENDING': 2, 'FAILED': 3, 'UNKNOWN': 99}
STATUS_INT_TO_STRING = {v: k for k, v in STATUS_STRING_TO_INT.items()}

engine = create_engine(config.ETH_DATABASE_URI, pool_size=40, max_overflow=100)
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = scoped_session(session_factory)

Base = declarative_base()

class ModelBase(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class BlockchainTask(ModelBase):
    __tablename__ = 'blockchain_task'

    signing_address = Column(String)

    contract = Column(String)
    function = Column(String)
    args = Column(JSON)
    kwargs = Column(JSON)

    transactions = relationship('BlockchainTransaction',
                                backref='blockchain_task',
                                lazy=True)

    @hybrid_property
    def status(self):
        lowest_status_code = min(set(t.status_code for t in self.transactions))
        return STATUS_INT_TO_STRING.get(lowest_status_code, 'UNKNOWN')

    @status.expression
    def status(cls):
        return (
            case(
                STATUS_INT_TO_STRING,
                value=(
                    select([func.min(BlockchainTransaction.status_code)])
                        .where(BlockchainTransaction.blockchain_task_id == cls.id)
                        .label('lowest_status')
                ),
                else_='UNKNOWN'
            )
        )

class BlockchainTransaction(ModelBase):
    __tablename__ = 'blockchain_transaction'

    signing_address = Column(String)

    _status = Column(String, default='PENDING')  # PENDING, SUCCESS, FAILED
    error = Column(String)
    message = Column(String)
    block = Column(Integer)
    submitted_date = Column(DateTime)
    mined_date = Column(DateTime)
    hash = Column(String)
    nonce = Column(Integer)
    nonce_consumed = Column(Boolean, default=False)

    blockchain_task_id = Column(Integer, ForeignKey(BlockchainTask.id))

    @hybrid_property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):

        if status not in STATUS_STRING_TO_INT:
            raise ValueError('Status {} not allowed. (Must be {}'.format(status, STATUS_STRING_TO_INT))

        self._status = status

    @hybrid_property
    def status_code(self):
        return STATUS_STRING_TO_INT.get(self._status, 99)

    @status_code.expression
    def status_code(cls):
        return(
            case(
                STATUS_STRING_TO_INT,
                value=cls._status,
                else_=99
            )
        )

    def __repr__(self):
        return ('<BlockchainTransaction ID:{} Nonce:{} Status: {}>'
                .format(self.id, self.nonce, self.status))
