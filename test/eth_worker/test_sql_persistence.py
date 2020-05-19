import os
import uuid
import pytest
import redis
from sqlalchemy.orm import scoped_session
from sqlalchemy.exc import IntegrityError

import config

from web3 import (
    Web3
)
from eth_keys import keys

from eth_worker.sql_persistence import engine, session_factory
from eth_worker.sql_persistence.interface import SQLPersistenceInterface
from eth_worker.sql_persistence.models import Base, BlockchainWallet, BlockchainTask, BlockchainTransaction


# @pytest.fixture(autouse=True)
# def mocker_web3(mocker):
#     mocker.patch('server.pusher_client.trigger')
#     mocker.patch('server.pusher_client.authenticate')
#     mocker.patch('server.pusher_client.trigger_batch')


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


# Just a randomly generated key. Needless to say, DON'T USE THIS FOR REAL FUNDS ANYWHERE
pk = '0x2bd62cccd89e375b2c248eaa123dc24141f7a8c6e384e045c0698ebaa1d62922'
address = '0x468F90c5a236130E5D51260A2A5Bfde834C694b6'

class TestModels:

    def test_create_wallet(self):

        wallet = BlockchainWallet()

        assert Web3.isChecksumAddress(wallet.address)
        pk = bytes.fromhex(wallet.private_key.replace('0x', ''))
        assert keys.PrivateKey(pk).public_key.to_checksum_address() == wallet.address
        assert wallet.encrypted_private_key != pk

    def test_create_wallet_from_pk(self):

        wallet = BlockchainWallet(pk)

        assert wallet.address == address

    def test_wallets_are_random(self):
        wallet_1 = BlockchainWallet()
        wallet_2 = BlockchainWallet()
        assert wallet_1.private_key != wallet_2.private_key

    def test_duplicate_wallets_cant_be_added(self, db_session):

        wallet_1 = BlockchainWallet(pk)
        wallet_2 = BlockchainWallet(pk)

        with pytest.raises(IntegrityError):
            db_session.add(wallet_1)
            db_session.add(wallet_2)
            db_session.commit()


    def test_task_relationships(self, db_session):

        prior = BlockchainTask(uuid=uuid.uuid4())

        posterior = BlockchainTask(uuid=uuid.uuid4())

        posterior.prior_tasks.append(prior)

        db_session.add_all([prior, posterior])
        db_session.commit()

        assert prior in posterior.prior_tasks
        assert posterior in prior.posterior_tasks

    def test_set_task_type(self, db_session):

        prior = BlockchainTask(uuid=uuid.uuid4())

        prior.type = 'SEND_ETH'

        assert prior.type == 'SEND_ETH'

        with pytest.raises(ValueError):
            prior.type = 'NOT_A_TYPE'

    def test_set_transaction_status(self, db_session):

        transaction = BlockchainTransaction()

        assert transaction.status == 'UNKNOWN'
        assert transaction.status_code == 99

        transaction.status = 'PENDING'

        assert transaction.status == 'PENDING'
        assert transaction.status_code == 2

        with pytest.raises(ValueError):
            transaction.status = 'NOT_A_STATUS'

        db_session.add(transaction)
        db_session.commit()

        # Uses a custom expression so worth testing the filter
        queried_transaction = db_session.query(BlockchainTransaction).filter(BlockchainTransaction.status_code == 2).first()
        assert queried_transaction == transaction


    def test_transaction_status_propagation(self, db_session):

        task = BlockchainTask(uuid=uuid.uuid4())

        assert task.status == 'UNSTARTED'

        transaction_1 = BlockchainTransaction()
        transaction_1.task = task
        transaction_1.status = 'PENDING'

        assert task.status == 'PENDING'

        transaction_2 = BlockchainTransaction()
        transaction_2.task = task
        transaction_2.status = 'SUCCESS'

        assert task.status == 'SUCCESS'
        assert task.status_code == 1

        db_session.add_all([task, transaction_1, transaction_2])
        db_session.commit()

        # Uses a custom expression so worth testing the filter
        queried_task = db_session.query(BlockchainTask).filter(BlockchainTask.status == 'SUCCESS').first()
        assert queried_task == task

# class TestInterface:
#
#     def test_claim_