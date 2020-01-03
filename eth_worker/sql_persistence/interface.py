import datetime
from sqlalchemy import and_, or_

from sempo_types import UUID

from sql_persistence.models import (
    session,
    BlockchainTransaction,
    BlockchainTask,
    BlockchainWallet
)

from eth_manager.exceptions import (
    WalletExistsError
)

class SQLPersistenceInterface(object):

    def _fail_expired_transactions(self):
        expire_time = datetime.datetime.utcnow() - datetime.timedelta(
            seconds=self.PENDING_TRANSACTION_EXPIRY_SECONDS
        )

        (session.query(BlockchainTransaction)
         .filter(and_(BlockchainTransaction.status == 'PENDING',
                      BlockchainTransaction.created < expire_time))
         .update({BlockchainTransaction.status: 'FAILED',
                  BlockchainTransaction.error: 'Timeout Error'},
                 synchronize_session=False))

    def _calculate_nonce(self, signing_wallet_obj, transaction_id, starting_nonce=0):

        self._fail_expired_transactions()

        # First find the highest *continuous* nonce that isn't either pending, or consumed
        # (failed or succeeded on blockchain)

        likely_consumed_nonces = (
            session.query(BlockchainTransaction)
                .filter(BlockchainTransaction.signing_wallet == signing_wallet_obj)
                .filter(BlockchainTransaction.ignore == False)
                .filter(BlockchainTransaction.first_block_hash == self.first_block_hash)
                .filter(
                    and_(
                        or_(BlockchainTransaction.nonce_consumed == True,
                            BlockchainTransaction.status == 'PENDING'),
                        BlockchainTransaction.nonce >= starting_nonce
                    )
                )
                .all())

        # Use a set to find continous nonces because txns in db may be out of order
        nonce_set = set()
        nonce_to_id = {}
        for txn in likely_consumed_nonces:
            nonce_set.add(txn.nonce)
            if txn.nonce > nonce_to_id.get(txn.nonce, 0):
                nonce_to_id[txn.nonce] = txn.id

        next_nonce = starting_nonce
        highest_valid_id = None
        while next_nonce in nonce_set:
            highest_valid_id = nonce_to_id.get(next_nonce, highest_valid_id)
            next_nonce += 1

        # if highest_valid_id is None, find it from db
        if highest_valid_id is None:
            highest_valid_txn = (
                session.query(BlockchainTransaction)
                    .filter(BlockchainTransaction.signing_wallet == signing_wallet_obj)
                    .filter(BlockchainTransaction.ignore == False)
                    .filter(BlockchainTransaction.first_block_hash == self.first_block_hash)
                    .filter(
                        and_(
                            or_(BlockchainTransaction.nonce_consumed == True,
                                BlockchainTransaction.status == 'PENDING'),
                            BlockchainTransaction.nonce <= starting_nonce
                        )
                    )
                    .order_by(BlockchainTransaction.id.desc())
                    .first())

            highest_valid_id = getattr(highest_valid_txn, 'id', 0)

        # Now find all transactions that are from the same address
        # and have a txn ID bound by the top consumed nonce and the current txn.
        # These txns are in a similar state to the current will be allocated nonces very shortly
        # Because they have lower IDs, they get precendent over the nonces

        live_txns_from_same_address = (
            session.query(BlockchainTransaction)
                .filter(BlockchainTransaction.signing_wallet == signing_wallet_obj)
                .filter(BlockchainTransaction.ignore == False)
                .filter(BlockchainTransaction.first_block_hash == self.first_block_hash)
                .filter(BlockchainTransaction.status == 'PENDING')
                .filter(and_(BlockchainTransaction.id > highest_valid_id,
                             BlockchainTransaction.id < transaction_id))
                .all())

        return next_nonce + len(live_txns_from_same_address)

    def claim_transaction_nonce(self, signing_wallet_obj, transaction_id):

        network_nonce = self.w3.eth.getTransactionCount(signing_wallet_obj.address, block_identifier='pending')

        blockchain_transaction = session.query(BlockchainTransaction).get(transaction_id)

        if blockchain_transaction.nonce is not None:
            return blockchain_transaction.nonce, blockchain_transaction.id

        calculated_nonce = self._calculate_nonce(signing_wallet_obj, transaction_id, network_nonce)

        blockchain_transaction.signing_wallet = signing_wallet_obj
        blockchain_transaction.nonce = calculated_nonce
        blockchain_transaction.status = 'PENDING'

        session.commit()

        gauranteed_clash_free = False

        clash_fix_attempts = 0
        while not gauranteed_clash_free and clash_fix_attempts < 200:
            clash_fix_attempts += 1
            # Occasionally two workers will hit the db at the same time and claim the same nonce

            nonce_clash_txns = (session.query(BlockchainTransaction)
                                .filter(BlockchainTransaction.id != transaction_id)
                                .filter(BlockchainTransaction.signing_wallet == signing_wallet_obj)
                                .filter(BlockchainTransaction.ignore == False)
                                .filter(BlockchainTransaction.first_block_hash == self.first_block_hash)
                                .filter(BlockchainTransaction.status == 'PENDING')
                                .filter(BlockchainTransaction.nonce == blockchain_transaction.nonce)
                                .all())

            if len(nonce_clash_txns) > 0:
                # If there is a clash, just try again
                print('\n ~~~~~~~~Cash Fix {} for txn {} with nonce {}~~~~~~~~'
                    .format(clash_fix_attempts, transaction_id, blockchain_transaction.nonce))
                print(nonce_clash_txns)

                lower_txn_ids = 0
                for txn in nonce_clash_txns:
                    if txn.id < transaction_id:
                        lower_txn_ids += 1

                if lower_txn_ids != 0:
                    print('Incrementing nonce by {}'.format(lower_txn_ids))
                    blockchain_transaction.nonce = blockchain_transaction.nonce + lower_txn_ids
                    session.commit()
                else:
                    print('Transaction has lowest ID, taking nonce')
                    gauranteed_clash_free = True

            else:
                gauranteed_clash_free = True

        session.commit()

        return calculated_nonce, blockchain_transaction.id

    def update_transaction_data(self, transaction_id, transaction_data):

        transaction = session.query(BlockchainTransaction).get(transaction_id)

        for attribute in transaction_data:
            setattr(transaction, attribute, transaction_data[attribute])

        session.commit()

    def create_blockchain_transaction(self, task_uuid):

        task = session.query(BlockchainTask).filter_by(uuid=task_uuid).first()

        blockchain_transaction = BlockchainTransaction(
            signing_wallet=task.signing_wallet,
            first_block_hash=self.first_block_hash
        )

        session.add(blockchain_transaction)

        if task:
            blockchain_transaction.task = task

        session.commit()

        return blockchain_transaction

    def get_transaction_hash_from_id(self, transaction_id):
        transaction = session.query(BlockchainTransaction).get(transaction_id)

        return transaction.hash

    def get_transaction_signing_wallet(self, transaction_id):

        transaction = session.query(BlockchainTransaction).get(transaction_id)

        return transaction.signing_wallet

    def get_unstarted_dependents(self, transaction_id):
        transaction = session.query(BlockchainTransaction).get(transaction_id)

        unstarted_dependents = []
        for dependent_task in transaction.task.dependents:
            if dependent_task.status == 'UNSTARTED':
                unstarted_dependents.append(dependent_task)

        return unstarted_dependents

    def unstatisfied_task_dependencies(self, task_uuid):
        task = session.query(BlockchainTask).filter_by(uuid=task_uuid).first()

        unsatisfied = []
        for dependee in task.dependees:
            if dependee.status != 'SUCCESS':
                unsatisfied.append(dependee)

        return unsatisfied

    def add_dependent_on_tasks(self, task, dependent_on_tasks):
        if dependent_on_tasks is None:
            dependent_on_tasks = []

        if isinstance(dependent_on_tasks, str):
            dependent_on_tasks = [dependent_on_tasks]

        for task_uuid in dependent_on_tasks:
            dependee_task = session.query(BlockchainTask).filter_by(uuid=task_uuid).first()
            task.dependees.append(dependee_task)

    def create_send_eth_task(self,
                             uuid: UUID,
                             signing_wallet_obj,
                             recipient_address, amount,
                             dependent_on_tasks=None):

        task = BlockchainTask(uuid,
                              signing_wallet=signing_wallet_obj,
                              type='SEND_ETH',
                              is_send_eth=True,
                              recipient_address=recipient_address,
                              amount=amount)

        session.add(task)

        self.add_dependent_on_tasks(task, dependent_on_tasks)

        session.commit()

        return task

    def create_function_task(self,
                             uuid: UUID,
                             signing_wallet_obj,
                             contract_address, abi_type,
                             function, args=None, kwargs=None,
                             gas_limit=None, dependent_on_tasks=None):

        task = BlockchainTask(uuid,
                              signing_wallet=signing_wallet_obj,
                              type='FUNCTION',
                              contract_address=contract_address,
                              abi_type=abi_type,
                              function=function,
                              args=args,
                              kwargs=kwargs,
                              gas_limit=gas_limit)

        session.add(task)

        self.add_dependent_on_tasks(task, dependent_on_tasks)

        session.commit()

        return task

    def create_deploy_contract_task(self,
                                    uuid: UUID,
                                    signing_wallet_obj,
                                    contract_name,
                                    args=None, kwargs=None,
                                    gas_limit=None, dependent_on_tasks=None):

        task = BlockchainTask(uuid,
                              signing_wallet=signing_wallet_obj,
                              type='DEPLOY_CONTRACT',
                              contract_name=contract_name,
                              args=args,
                              kwargs=kwargs,
                              gas_limit=gas_limit)

        session.add(task)

        self.add_dependent_on_tasks(task, dependent_on_tasks)

        session.commit()

        return task

    def get_serialised_task_from_uuid(self, uuid):
        task = self.get_task_from_uuid(uuid)

        if task is None:
            ttt = 4
            return None

        base_data = {
            'id': task.id,
            'status': task.status,
            'dependents': [task.uuid for task in task.dependents],
            'dependees': [task.uuid for task in task.dependees]
        }

        if task.successful_transaction:

            transaction_data = {
                'successful_hash': task.successful_transaction.hash,
                'successful_block': task.successful_transaction.block,
                'contract_address': task.successful_transaction.contract_address
            }

            return {**transaction_data, **base_data}

        else:
            return base_data

    def get_task_from_uuid(self, task_uuid):
        return session.query(BlockchainTask).filter_by(uuid=task_uuid).first()

    def create_blockchain_wallet_from_encrypted_private_key(self, encrypted_private_key):

        private_key = BlockchainWallet.decrypt_private_key(encrypted_private_key)
        self.create_blockchain_wallet_from_private_key(private_key)

    def create_blockchain_wallet_from_private_key(self, private_key,
                                                  allow_existing=False,
                                                  wei_target_balance=0,
                                                  wei_topup_threshold=0,
                                                  ):

        address = BlockchainWallet.address_from_private_key(private_key)

        existing_wallet = session.query(BlockchainWallet).filter_by(address=address).first()
        if existing_wallet:
            if allow_existing:
                return existing_wallet
            else:
                raise WalletExistsError("Account for provided private key already exists")

        wallet = BlockchainWallet(
            private_key=private_key,
            wei_target_balance=wei_target_balance,
            wei_topup_threshold=wei_topup_threshold)

        session.add(wallet)

        session.commit()

        return wallet

    def create_new_blockchain_wallet(self, wei_target_balance=0, wei_topup_threshold=0, private_key=None):

        if private_key:
            return self.create_blockchain_wallet_from_private_key(
                private_key,
                True,
                wei_target_balance,
                wei_topup_threshold,
            )

        wallet = BlockchainWallet(wei_target_balance=wei_target_balance,
                                  wei_topup_threshold=wei_topup_threshold)

        session.add(wallet)

        session.commit()

        return wallet


    def get_all_wallets(self):
        return session.query(BlockchainWallet).all()

    def get_wallet_by_address(self, address):
        return session.query(BlockchainWallet).filter(BlockchainWallet.address == address).first()

    def get_wallet_by_encrypted_private_key(self, encrypted_private_key):
         return session.query(BlockchainWallet).filter(
             BlockchainWallet.encrypted_private_key == encrypted_private_key).first()

    def set_wallet_last_topup_task_uuid(self, wallet_address, task_uuid):
        wallet = self.get_wallet_by_address(wallet_address)
        wallet.last_topup_task_uuid = task_uuid

        session.commit()

    def __init__(self, w3, PENDING_TRANSACTION_EXPIRY_SECONDS=300):

        self.w3 = w3

        self.first_block_hash = w3.eth.getBlock(0).hash.hex()

        self.PENDING_TRANSACTION_EXPIRY_SECONDS = PENDING_TRANSACTION_EXPIRY_SECONDS