from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref, object_session
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Table, Column, Integer, String, DateTime, Boolean, ForeignKey, BigInteger, JSON, Numeric
from sqlalchemy.orm import scoped_session
from sqlalchemy import select, func, case, event

import requests
import time
from requests.auth import HTTPBasicAuth
import datetime, base64, os
from cryptography.fernet import Fernet
from eth_utils import keccak
from eth_keys import keys
from web3 import Web3

from sempo_types import UUID, UUIDList
import config

ALLOWED_TASK_TYPES = ['SEND_ETH', 'FUNCTION', 'DEPLOY_CONTRACT']
STATUS_STRING_TO_INT = {'SUCCESS': 1, 'PENDING': 2, 'UNSTARTED': 3, 'FAILED': 4, 'UNKNOWN': 99}
STATUS_INT_TO_STRING = {v: k for k, v in STATUS_STRING_TO_INT.items()}

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

    signing_wallet_id = Column(Integer, ForeignKey(BlockchainWallet.id), index=True)

    reverses_id = Column(Integer, ForeignKey('blockchain_task.id'), index=True)

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
    def status_code(self) -> int:
        """
        For all the transactions associated with this task, get the lowest status code
        """
        return min(set(t.status_code for t in self.transactions) or [3])

    @hybrid_property
    def status(self) -> str:
        """
        Human-friendly string of the status code
        """
        return STATUS_INT_TO_STRING.get(self.status_code, 'UNSTARTED')

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

    def add_prior_tasks(self, prior_tasks: UUIDList):
        self._add_dependency_relationships(prior_tasks, self.prior_tasks)

    def add_posterior_tasks(self, posterior_tasks: UUIDList):
        self._add_dependency_relationships(posterior_tasks, self.posterior_tasks)

    def _add_dependency_relationships(self, tasks_uuids: UUIDList, dependency_relationship):
        if tasks_uuids is None:
            return

        if isinstance(tasks_uuids, str):
            tasks_uuids = [tasks_uuids]

        for task_uuid in tasks_uuids:
            # TODO: Make sure this can't be failed due to a race condition on tasks being added
            task = object_session(self).query(BlockchainTask).filter_by(uuid=task_uuid).first()
            if task:
                dependency_relationship.append(task)

    def __init__(
            self,
            uuid: UUID,
            prior_tasks: Optional[UUIDList]=None,
            posterior_tasks: Optional[UUIDList]=None, **kwargs
    ):
        super(BlockchainTask, self).__init__(**kwargs)

        self.uuid = uuid

        self.previous_invocations = 0

        if prior_tasks:
            self.add_prior_tasks(prior_tasks)

        if posterior_tasks:
            self.add_posterior_tasks(posterior_tasks)


class BlockchainTransaction(ModelBase):
    __tablename__ = 'blockchain_transaction'

    _status = Column(String, default='PENDING', index=True)  # PENDING, SUCCESS, FAILED
    error = Column(String)
    message = Column(String)
    block = Column(Integer)
    submitted_date = Column(DateTime, index=True)
    mined_date = Column(DateTime)
    hash = Column(String)
    contract_address = Column(String)
    nonce = Column(Integer)
    nonce_consumed = Column(Boolean, default=False, index=True)

    sender_address = Column(String)
    recipient_address = Column(String)
    amount = Column(Numeric(27))
    is_synchronized_with_app = Column(Boolean, default=False)
    is_third_party_transaction = Column(Boolean, default=False)

    ignore = Column(Boolean, default=False)

    first_block_hash = Column(String, index=True)

    signing_wallet_id = Column(Integer, ForeignKey(BlockchainWallet.id), index=True)

    blockchain_task_id = Column(Integer, ForeignKey(BlockchainTask.id), index=True)

    blockchain_task = relationship('BlockchainTask', foreign_keys=[blockchain_task_id])

    @hybrid_property
    def status(self):
        return self._status or 'UNKNOWN'

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

class SynchronizedBlock(ModelBase):
    __tablename__ = 'synchronized_block'
    block_number = Column(Integer, index=True)
    status = Column(String)
    is_synchronized = Column(Boolean)
    synchronization_filter_id = Column(Integer, ForeignKey('synchronization_filter.id'), index=True)
    synchronization_filter = relationship("SynchronizationFilter", back_populates="blocks", lazy=True)
    decimals = Column(Integer)

class SynchronizationFilter(ModelBase):
    __tablename__ = 'synchronization_filter'
    contract_address = Column(String, unique=True)
    contract_type = Column(String)
    filter_parameters = Column(String)
    filter_type = Column(String) # TRANSFER, EXCHANGE
    max_block = Column(Integer)
    decimals = Column(Integer)
    blocks = relationship("SynchronizedBlock", back_populates="synchronization_filter", lazy=True)

# When BlockchainTransaction is updated, let the api layer know about it
@event.listens_for(BlockchainTransaction, 'after_update')
def receive_after_update(mapper, connection, target):
    if target.blockchain_task and not target.is_third_party_transaction:
        post_data = {
                'blockchain_task_uuid': target.blockchain_task.uuid,
                'timestamp': time.time(),
                'blockchain_status': target.status,
                'error': target.error,
                'message': target.message,
                'hash': target.hash
            }
        callback_url = config.APP_HOST + '/api/v1/blockchain_taskable'

        try:
            r = requests.post(
                callback_url,
                timeout=5,
                json=post_data,
                auth=HTTPBasicAuth(config.INTERNAL_AUTH_USERNAME,
                                   config.INTERNAL_AUTH_PASSWORD)
            )
        except Exception:
            r = None

        if r and r.ok:
            obj_table = BlockchainTransaction.__table__
            connection.execute(
                obj_table.update().
                where(obj_table.c.id == target.id).
                values(is_synchronized_with_app=True)
            )
        else:
            # NOTE: Soft error handling here for now, as incomplete transactions can always be synched later
            # where is_synchronized_with_app=False

            if r is not None and r.json().get('message') is not None:
                config.logg.warning(f"App side sync error: {r.json().get('message')}")
            else:
                config.logg.warning(f"Could not reach 'APP_HOST' URL: {callback_url}. Please check your config.ini'")
            obj_table = BlockchainTransaction.__table__
            connection.execute(
                obj_table.update().
                where(obj_table.c.id == target.id).
                values(is_synchronized_with_app=False)
            )
