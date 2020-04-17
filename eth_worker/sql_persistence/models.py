from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Table, Column, Integer, String, DateTime, Boolean, ForeignKey, BigInteger, JSON, Numeric
from sqlalchemy.orm import scoped_session
from sqlalchemy import select, func, case
import datetime, base64, os
from cryptography.fernet import Fernet
from eth_utils import keccak
from eth_keys import keys
from web3 import Web3

from sempo_types import UUID
import config

ALLOWED_TASK_TYPES = ['SEND_ETH', 'FUNCTION', 'DEPLOY_CONTRACT']
STATUS_STRING_TO_INT = {'SUCCESS': 1, 'PENDING': 2, 'UNSTARTED': 3, 'FAILED': 4, 'UNKNOWN': 99}
STATUS_INT_TO_STRING = {v: k for k, v in STATUS_STRING_TO_INT.items()}

engine = create_engine(
    config.ETH_DATABASE_URI,
    pool_size=config.ETH_WORKER_DB_POOL_SIZE,
    max_overflow=config.ETH_WORKER_DB_POOL_OVERFLOW
)

session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = scoped_session(session_factory)

Base = declarative_base()


class ModelBase(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class BlockchainWallet(ModelBase):
    __tablename__ = 'blockchain_wallet'

    address = Column(String(), index=True, unique=True)
    _encrypted_private_key = Column(String())

    wei_target_balance    = Column(BigInteger())
    wei_topup_threshold   = Column(BigInteger())
    last_topup_task_uuid    = Column(String())

    tasks = relationship('BlockchainTask',
                         backref='signing_wallet',
                         lazy=True,
                         foreign_keys='BlockchainTask.signing_wallet_id')

    transactions = relationship('BlockchainTransaction',
                                backref='signing_wallet',
                                lazy=True,
                                foreign_keys='BlockchainTransaction.signing_wallet_id')

    @hybrid_property
    def encrypted_private_key(self):
        return self._encrypted_private_key

    @encrypted_private_key.setter
    def encrypted_private_key(self, value):
        self._encrypted_private_key = value
        private_key = self.decrypt_private_key(value)
        self.address = self.address_from_private_key(private_key)

    @hybrid_property
    def private_key(self):
        return self.decrypt_private_key(self._encrypted_private_key)

    @private_key.setter
    def private_key(self, value):
        self.encrypted_private_key = self.encrypt_private_key(value)
        self.address = self.address_from_private_key(value)

    @staticmethod
    def decrypt_private_key(encrypted_private_key):
        encrypted_private_key_bytes = BlockchainWallet._bytify_if_required(encrypted_private_key)

        return BlockchainWallet._cipher_suite() \
            .decrypt(encrypted_private_key_bytes).decode('utf-8')

    @staticmethod
    def encrypt_private_key(private_key):
        private_key_bytes = BlockchainWallet._bytify_if_required(private_key)

        return BlockchainWallet._cipher_suite()\
            .encrypt(private_key_bytes).decode('utf-8')

    @staticmethod
    def _bytify_if_required(string):
        return string if isinstance(string, bytes) else string.encode('utf-8')

    @staticmethod
    def _cipher_suite():
        fernet_encryption_key = base64.b64encode(keccak(text=config.SECRET_KEY))
        return Fernet(fernet_encryption_key)

    @staticmethod
    def address_from_private_key(private_key):
        if isinstance(private_key, str):
            private_key = bytes.fromhex(private_key.replace('0x', ''))
        return keys.PrivateKey(private_key).public_key.to_checksum_address()

    def __init__(self, private_key=None, wei_target_balance=None, wei_topup_threshold=None):

        if private_key:
            self.private_key = private_key
        else:
            self.private_key = Web3.toHex(keccak(os.urandom(4096)))

        self.wei_target_balance = wei_target_balance
        self.wei_topup_threshold = wei_topup_threshold

# https://stackoverflow.com/questions/20830118/creating-a-self-referencing-m2m-relationship-in-sqlalchemy-flask
task_dependencies = Table(
    'task_dependencies', Base.metadata,
    Column('prior_task_id', Integer, ForeignKey('blockchain_task.id'), primary_key=True),
    Column('posterior_task_id', Integer, ForeignKey('blockchain_task.id'), primary_key=True)
)

class BlockchainTask(ModelBase):
    __tablename__ = 'blockchain_task'

    uuid = Column(String, index=True)

    _type = Column(String)
    contract_address = Column(String)
    contract_name = Column(String)
    abi_type = Column(String)
    function = Column(String)
    args = Column(JSON)
    kwargs = Column(JSON)
    gas_limit = Column(BigInteger)

    is_send_eth = Column(Boolean, default=False)
    recipient_address = Column(String)
    _amount = Column(Numeric(27))

    signing_wallet_id = Column(Integer, ForeignKey(BlockchainWallet.id))

    reverses_id = Column(Integer, ForeignKey('blockchain_task.id'))

    # Purely for convenience to show status on single db table for debugging - use status hybrid prop in code
    status_text = Column(String)

    # How many times the system has previously requested an attempt to complete a transaction for this task
    previous_invocations = Column(Integer)

    transactions = relationship('BlockchainTransaction',
                                backref='task',
                                lazy=True)

    reversed_by = relationship("BlockchainTask",
                               backref=backref('reverses', remote_side="BlockchainTask.id"),
                               foreign_keys='BlockchainTask.reverses_id')

    prior_tasks = relationship('BlockchainTask',
                             secondary=task_dependencies,
                             primaryjoin="BlockchainTask.id == task_dependencies.c.posterior_task_id",
                             secondaryjoin="BlockchainTask.id == task_dependencies.c.prior_task_id",
                             backref='posterior_tasks')



    @hybrid_property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        print('SETTER 3!')
        print(value)
        print(self)
        print(self.status_text)
        print('---')
        if value not in ALLOWED_TASK_TYPES:
            raise ValueError(f'{value} not in allow task types')
        self._type = value

    @hybrid_property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self, val):
        self._amount = val

    @hybrid_property
    def successful_transaction(self):
        for t in self.transactions:
            if t.status == 'SUCCESS':
                return t
        return None

    @hybrid_property
    def status(self):
        lowest_status_code = min(set(t.status_code for t in self.transactions) or [3])
        return STATUS_INT_TO_STRING.get(lowest_status_code, 'UNSTARTED')

    @status.expression
    def status(status):
        return (
            case(
                STATUS_INT_TO_STRING,
                value=(
                    select([func.min(BlockchainTransaction.status_code)])
                        .where(BlockchainTransaction.blockchain_task_id == status.id)
                        .label('lowest_status')
                ),
                else_='UNSTARTED'
            )
        )

    def __init__(self, uuid: UUID, **kwargs):
        super(BlockchainTask, self).__init__(**kwargs)

        self.uuid = uuid

        self.previous_invocations = 0

class BlockchainTransaction(ModelBase):
    __tablename__ = 'blockchain_transaction'

    _status = Column(String, default='PENDING')  # PENDING, SUCCESS, FAILED
    error = Column(String)
    message = Column(String)
    block = Column(Integer)
    submitted_date = Column(DateTime)
    mined_date = Column(DateTime)
    hash = Column(String)
    contract_address = Column(String)
    nonce = Column(Integer)
    nonce_consumed = Column(Boolean, default=False)

    is_synchronized_with_app = Column(Boolean, default=False)

    ignore = Column(Boolean, default=False)

    first_block_hash = Column(String)

    signing_wallet_id = Column(Integer, ForeignKey(BlockchainWallet.id))

    blockchain_task_id = Column(Integer, ForeignKey(BlockchainTask.id))

    @hybrid_property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        print('SETTER 2!')
        print(value)
        print(self)
        print(self.message)
        print(self.block)
        print(self.hash)
        print(self.contract_address)
        print(self.signing_wallet_id)
        print(self.blockchain_task_id)
        # Put POST here
        # Want to send current timestamp
        # Want to send lookup(blockchain_task_id).uuid
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