from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Table, Column, Integer, String, DateTime, Boolean, ForeignKey, BigInteger, JSON
from sqlalchemy.orm import scoped_session
from sqlalchemy import select, func, case
import datetime, base64, os
from cryptography.fernet import Fernet
from eth_utils import keccak
from eth_keys import keys
from web3 import Web3

import config

STATUS_STRING_TO_INT = {'SUCCESS': 1, 'PENDING': 2, 'UNSTARTED': 3, 'FAILED': 4, 'UNKNOWN': 99}
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

class BlockchainAddress(ModelBase):
    __tablename__ = 'blockchain_address'

    address = Column(String(), index=True, unique=True)
    _encrypted_private_key = Column(String())

    tasks = relationship('BlockchainTask',
                         backref='signing_address',
                         lazy=True,
                         foreign_keys='BlockchainTask.signing_address_id')

    transactions = relationship('BlockchainTransaction',
                                backref='signing_address',
                                lazy=True,
                                foreign_keys='BlockchainTransaction.signing_address_id')

    @hybrid_property
    def encrypted_private_key(self):
        return self._encrypted_private_key

    @encrypted_private_key.setter
    def encrypted_private_key(self, value):
        self._encrypted_private_key = value
        private_key = self.decrypt_private_key(value)
        self._set_address_from_private_key(private_key)

    @hybrid_property
    def private_key(self):
        return self.decrypt_private_key(self._encrypted_private_key)

    @private_key.setter
    def private_key(self, value):
        self.encrypted_private_key = self.encrypt_private_key(value)
        self._set_address_from_private_key(value)

    @staticmethod
    def decrypt_private_key(encrypted_private_key):
        return BlockchainAddress._cipher_suite() \
            .decrypt(encrypted_private_key.encode('utf-8')).decode('utf-8')
    @staticmethod
    def encrypt_private_key(private_key):
        return BlockchainAddress._cipher_suite()\
            .encrypt(private_key.encode('utf-8')).decode('utf-8')

    @staticmethod
    def _cipher_suite():
        fernet_encryption_key = base64.b64encode(keccak(text=config.SECRET_KEY))
        return Fernet(fernet_encryption_key)

    def _set_address_from_private_key(self, private_key):
        if isinstance(private_key, str):
            private_key = bytearray.fromhex(private_key.replace('0x', ''))

        self.address = keys.PrivateKey(private_key).public_key.to_checksum_address()

    def __init__(self, encrypted_private_key=None):

        if encrypted_private_key:
            self.encrypted_private_key = encrypted_private_key
        else:
            self.private_key = Web3.toHex(keccak(os.urandom(4096)))

# https://stackoverflow.com/questions/20830118/creating-a-self-referencing-m2m-relationship-in-sqlalchemy-flask
task_dependencies = Table(
    'task_dependencies', Base.metadata,
    Column('dependent_task_id', Integer, ForeignKey('blockchain_task.id'), primary_key=True),
    Column('dependee_task_id', Integer, ForeignKey('blockchain_task.id'), primary_key=True)
)

class BlockchainTask(ModelBase):
    __tablename__ = 'blockchain_task'

    contract = Column(String)
    function = Column(String)
    args = Column(JSON)
    kwargs = Column(JSON)
    gas_limit = Column(BigInteger)

    is_send_eth = Column(Boolean, default=False)
    recipient_address = Column(String)
    amount = Column(BigInteger)

    signing_address_id = Column(Integer, ForeignKey(BlockchainAddress.id))

    transactions = relationship('BlockchainTransaction',
                                backref='task',
                                lazy=True)

    dependees = relationship('BlockchainTask',
                             secondary=task_dependencies,
                             primaryjoin="BlockchainTask.id == task_dependencies.c.dependee_task_id",
                             secondaryjoin="BlockchainTask.id == task_dependencies.c.dependent_task_id",
                             backref='dependents')

    @hybrid_property
    def status(self):
        lowest_status_code = min(set(t.status_code for t in self.transactions) or [3])
        return STATUS_INT_TO_STRING.get(lowest_status_code, 'UNSTARTED')

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
                else_='UNSTARTED'
            )
        )

class BlockchainTransaction(ModelBase):
    __tablename__ = 'blockchain_transaction'

    _status = Column(String, default='PENDING')  # PENDING, SUCCESS, FAILED
    error = Column(String)
    message = Column(String)
    block = Column(Integer)
    submitted_date = Column(DateTime)
    mined_date = Column(DateTime)
    hash = Column(String)
    nonce = Column(Integer)
    nonce_consumed = Column(Boolean, default=False)

    signing_address_id = Column(Integer, ForeignKey(BlockchainAddress.id))

    blockchain_task_id = Column(Integer, ForeignKey(BlockchainTask.id))

    @hybrid_property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):

        if value not in STATUS_STRING_TO_INT:
            raise ValueError('Status {} not allowed. (Must be {}'.format(value, STATUS_STRING_TO_INT))

        self._status = value

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