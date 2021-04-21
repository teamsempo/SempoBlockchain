import pytest
from sqlalchemy.exc import IntegrityError

from web3 import (
    Web3
)
from eth_keys import keys

from sql_persistence.interface import SQLPersistenceInterface
from sql_persistence.models import BlockchainWallet, BlockchainTask, BlockchainTransaction

from utils import str_uuid, keypair

class TestModels:

    def test_create_wallet(self):

        wallet = BlockchainWallet()

        assert Web3.isChecksumAddress(wallet.address)
        pk = bytes.fromhex(wallet.private_key.replace('0x', ''))
        assert keys.PrivateKey(pk).public_key.to_checksum_address() == wallet.address
        assert wallet.encrypted_private_key != pk

    def test_create_wallet_from_pk(self):

        pair = keypair()

        wallet = BlockchainWallet(pair['pk'])

        assert wallet.address == pair['address']

    def test_wallets_are_random(self):
        wallet_1 = BlockchainWallet()
        wallet_2 = BlockchainWallet()
        assert wallet_1.private_key != wallet_2.private_key

    def test_duplicate_wallets_cant_be_added(self, db_session):

        common_pk = keypair()['pk']

        wallet_1 = BlockchainWallet(common_pk)
        wallet_2 = BlockchainWallet(common_pk)

        with pytest.raises(IntegrityError):
            db_session.add(wallet_1)
            db_session.add(wallet_2)
            db_session.commit()


    def test_task_relationships(self, db_session):

        prior = BlockchainTask(uuid=str_uuid())

        posterior = BlockchainTask(uuid=str_uuid())

        posterior.prior_tasks.append(prior)

        db_session.add_all([prior, posterior])
        db_session.commit()

        assert prior in posterior.prior_tasks
        assert posterior in prior.posterior_tasks

    def test_set_task_type(self, db_session):

        prior = BlockchainTask(uuid=str_uuid())

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

        task = BlockchainTask(uuid=str_uuid())

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

class TestInterface:

    def test_claim_transaction_nonce(self, db_session, persistence_module: SQLPersistenceInterface):
        def created_nonced_transaction():
            t = BlockchainTransaction(first_block_hash=persistence_module.first_block_hash)
            t.signing_wallet = wallet
            db_session.add(t)
            db_session.commit()

            nonce = persistence_module.locked_claim_transaction_nonce(
                network_nonce=starting_nonce,
                signing_wallet_id=wallet.id,
                transaction_id=t.id
            )

            t.nonce_consumed = True

            return t, nonce


        wallet = BlockchainWallet()
        db_session.add(wallet)

        starting_nonce = 4
        transactions = []
        for i in range(0, 3):
            trans, nonce = created_nonced_transaction()
            transactions.append(trans)
            assert nonce == starting_nonce + i

        for t in transactions:
            t.nonce_consumed = False

        transactions[0].status = 'FAILED'

        trans, nonce = created_nonced_transaction()
        transactions.append(trans)

        assert trans.nonce == starting_nonce

        # TODO: Work out if this part should pass
        # transactions[-1].status = 'SUCCESS'
        # trans, nonce = created_nonced_transaction()
        # transactions.append(trans)
        # assert trans.nonce == starting_nonce + 1

    def test_update_transaction_data(self, db_session, persistence_module: SQLPersistenceInterface):
        transaction = BlockchainTransaction()
        db_session.add(transaction)

        db_session.commit()

        persistence_module.update_transaction_data(
            transaction.id,
            {'status': 'SUCCESS', 'ignore': True}
        )

        assert transaction.status == 'SUCCESS'
        assert transaction.ignore is True

    def test_create_blockchain_transaction(self, db_session, persistence_module: SQLPersistenceInterface):

        wallet = BlockchainWallet()
        db_session.add(wallet)

        task = BlockchainTask(str_uuid())
        task.signing_wallet = wallet
        db_session.add(task)

        trans = persistence_module.create_blockchain_transaction(task_uuid=task.uuid)

        assert trans.task.uuid == task.uuid

    def test_create_function_task(self, db_session, persistence_module: SQLPersistenceInterface):

        signing_wallet_obj = BlockchainWallet()
        db_session.add(signing_wallet_obj)

        uuid = str_uuid()
        contract_address = '0x1234'
        abi_type = "ERC20" # aka contract_type
        function_name = "transferFrom"
        args = ['0x1234', '0x2345', int(1e36)]
        kwargs = None
        signing_address = None
        encrypted_private_key = None
        gas_limit = None
        prior_tasks = None
        reserves_task = None

        trans = persistence_module.create_function_task(uuid,
                signing_wallet_obj,
                contract_address, abi_type,
                function_name, args, kwargs,
                gas_limit, prior_tasks, reserves_task)

        assert trans.uuid == uuid
        assert trans.type == 'FUNCTION'

    def test_deploy_contract_test(self, db_session, persistence_module: SQLPersistenceInterface):
        signing_wallet_obj = BlockchainWallet()
        db_session.add(signing_wallet_obj)

        uuid = str_uuid()
        contract_name = 'ERC20'
        args = []
        kwargs = None
        gas_limit = None
        prior_tasks = None

        trans = persistence_module.create_deploy_contract_task(
                uuid,
                signing_wallet_obj,
                contract_name,
                args, kwargs,
                gas_limit, prior_tasks)

        assert trans.uuid == uuid
        assert trans.type == 'DEPLOY_CONTRACT'

    def test_create_blockchain_wallet_from_private_key(self, db_session, persistence_module: SQLPersistenceInterface):

        from utils import keypair

        kp = keypair()

        trans = persistence_module.create_blockchain_wallet_from_private_key(kp['pk'])

        assert trans.address == kp['address']


    @pytest.mark.xfail(reason="SQL Testing Weirdness causes this to be problematic")
    def test_add_prior_tasks(self, db_session, persistence_module: SQLPersistenceInterface):

        prior_1 = BlockchainTask(uuid=str_uuid())
        prior_2 = BlockchainTask(uuid=str_uuid())
        uuid_1 = prior_1.uuid
        uuid_2 = prior_2.uuid

        posterior = BlockchainTask(uuid=str_uuid())

        db_session.add_all([prior_1, prior_2, posterior])
        db_session.commit()

        posterior.add_prior_tasks([uuid_1, uuid_2])

        assert prior_1 in posterior.prior_tasks
        assert prior_2 in posterior.prior_tasks

