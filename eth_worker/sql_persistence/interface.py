import datetime
from sqlalchemy import and_, or_

from sempo_types import UUID, UUIDList

from sql_persistence.models import (
    BlockchainTransaction,
    BlockchainTask,
    BlockchainWallet
)

from eth_manager.exceptions import (
    WalletExistsError,
    LockedNotAcquired
)
from sqlalchemy.orm import scoped_session

class SQLPersistenceInterface(object):

    def _fail_expired_transactions(self):
        expire_time = datetime.datetime.utcnow() - datetime.timedelta(
            seconds=self.PENDING_TRANSACTION_EXPIRY_SECONDS
        )

        (self.session.query(BlockchainTransaction)
         .filter(and_(BlockchainTransaction.status == 'PENDING',
                      BlockchainTransaction.updated < expire_time))
         .update({BlockchainTransaction.status: 'FAILED',
                  BlockchainTransaction.error: 'Timeout Error'},
                 synchronize_session=False))

    def _unconsume_high_failed_nonces(self, signing_wallet_id, stating_nonce):
        expire_time = datetime.datetime.utcnow() - datetime.timedelta(
            seconds=self.PENDING_TRANSACTION_EXPIRY_SECONDS
        )

        highest_known_success = (self.session.query(BlockchainTransaction)
                                 .filter(and_(BlockchainTransaction.signing_wallet_id == signing_wallet_id,
                                              BlockchainTransaction.status == 'SUCCESS'))
                                 .order_by(BlockchainTransaction.id.desc()).first()
                                 )

        if highest_known_success:
            highest_known_nonce = highest_known_success.nonce or 0
        else:
            highest_known_nonce = 0

        nonce = max(stating_nonce, highest_known_nonce)

        (self.session.query(BlockchainTransaction)
         .filter(and_(BlockchainTransaction.signing_wallet_id == signing_wallet_id,
                      BlockchainTransaction.status == 'FAILED',
                      BlockchainTransaction.nonce > nonce,
                      BlockchainTransaction.submitted_date < expire_time))
         .update({BlockchainTransaction.nonce_consumed: False},
                 synchronize_session=False))

    def _calculate_nonce(self, signing_wallet_obj, starting_nonce=0):

        self._unconsume_high_failed_nonces(signing_wallet_obj.id, starting_nonce)
        self._fail_expired_transactions()

        # First find the highest *continuous* nonce that isn't either pending, or consumed
        # (failed or succeeded on blockchain)

        likely_consumed_nonces = (
            self.session.query(BlockchainTransaction)
                .filter(BlockchainTransaction.signing_wallet == signing_wallet_obj)
                .filter(BlockchainTransaction.ignore == False)
                .filter(BlockchainTransaction.first_block_hash == self.first_block_hash)
                .filter(
                    and_(
                        or_(BlockchainTransaction.status == 'PENDING',
                            BlockchainTransaction.nonce_consumed == True),
                        BlockchainTransaction.nonce >= starting_nonce
                    )
                )
                .all())

        # Use a set to find continous nonces because txns in db may be out of order
        nonce_set = set()
        for txn in likely_consumed_nonces:
            nonce_set.add(txn.nonce)

        next_nonce = starting_nonce
        while next_nonce in nonce_set:
            next_nonce += 1

        return next_nonce

    def locked_claim_transaction_nonce(self, signing_wallet_obj, transaction_id):
        # Locks normally get released in less than 0.05 seconds

        have_lock = False
        lock = self.red.lock(signing_wallet_obj.address, timeout=10)

        print(f'Attempting lock for txn: {transaction_id} \n'
              f'addr:{signing_wallet_obj.address}')

        try:
            have_lock = lock.acquire(blocking_timeout=1)
            if have_lock:
                return self.claim_transaction_nonce(signing_wallet_obj, transaction_id)
            else:
                print(f'Lock not acquired for txn: {transaction_id} \n'
                      f'addr:{signing_wallet_obj.address}')
                raise LockedNotAcquired
        finally:
            if have_lock:
                lock.release()

    def claim_transaction_nonce(self, signing_wallet_obj, transaction_id):

        network_nonce = self.w3.eth.getTransactionCount(signing_wallet_obj.address, block_identifier='pending')

        blockchain_transaction = self.session.query(BlockchainTransaction).get(transaction_id)

        if blockchain_transaction.nonce is not None:
            return blockchain_transaction.nonce, blockchain_transaction.id

        calculated_nonce = self._calculate_nonce(signing_wallet_obj, network_nonce)

        blockchain_transaction.signing_wallet = signing_wallet_obj
        blockchain_transaction.nonce = calculated_nonce
        blockchain_transaction.status = 'PENDING'

        self.session.commit()

        return calculated_nonce, blockchain_transaction.id

    def update_transaction_data(self, transaction_id, transaction_data):

        transaction = self.session.query(BlockchainTransaction).get(transaction_id)

        for attribute in transaction_data:
            setattr(transaction, attribute, transaction_data[attribute])

        self.session.commit()

    def create_blockchain_transaction(self, task_uuid):

        task = self.session.query(BlockchainTask).filter_by(uuid=task_uuid).first()

        blockchain_transaction = BlockchainTransaction(
            signing_wallet=task.signing_wallet,
            first_block_hash=self.first_block_hash
        )

        self.session.add(blockchain_transaction)

        if task:
            blockchain_transaction.task = task

        self.session.commit()

        return blockchain_transaction

    def get_transaction(self, transaction_id):
        return self.session.query(BlockchainTransaction).get(transaction_id)

    def get_transaction_signing_wallet(self, transaction_id):

        transaction = self.session.query(BlockchainTransaction).get(transaction_id)

        return transaction.signing_wallet

    def add_prior_tasks(self, task: BlockchainTask, prior_tasks: UUIDList):
        if prior_tasks is None:
            prior_tasks = []

        if isinstance(prior_tasks, str):
            prior_tasks = [prior_tasks]

        for task_uuid in prior_tasks:
            # TODO: Make sure this can't be failed due to a race condition on tasks being added
            prior_task = self.session.query(BlockchainTask).filter_by(uuid=task_uuid).first()
            if prior_task:
                task.prior_tasks.append(prior_task)

    def add_posterior_tasks(self, task: BlockchainTask, posterior_tasks: UUIDList):
        if posterior_tasks is None:
            posterior_tasks = []

        if isinstance(posterior_tasks, str):
            posterior_tasks = [posterior_tasks]

        for task_uuid in posterior_tasks:
            # TODO: Make sure this can't be failed due to a race condition on tasks being added
            posterior = self.session.query(BlockchainTask).filter_by(uuid=task_uuid).first()
            if posterior:
                task.posterior_tasks.append(posterior)

    def set_task_status_text(self, task, text):
        task.status_text = text
        self.session.commit()

    def create_send_eth_task(self,
                             uuid: UUID,
                             signing_wallet_obj,
                             recipient_address, amount,
                             prior_tasks=None,
                             posterior_tasks=None):

        task = BlockchainTask(uuid,
                              signing_wallet=signing_wallet_obj,
                              type='SEND_ETH',
                              is_send_eth=True,
                              recipient_address=recipient_address,
                              amount=amount)

        self.session.add(task)

        self.add_prior_tasks(task, prior_tasks)
        self.add_posterior_tasks(task, posterior_tasks)

        self.session.commit()

        return task

    def create_function_task(self,
                             uuid: UUID,
                             signing_wallet_obj,
                             contract_address, abi_type,
                             function, args=None, kwargs=None,
                             gas_limit=None, prior_tasks=None, reverses_task=None):

        task = BlockchainTask(uuid,
                              signing_wallet=signing_wallet_obj,
                              type='FUNCTION',
                              contract_address=contract_address,
                              abi_type=abi_type,
                              function=function,
                              args=args,
                              kwargs=kwargs,
                              gas_limit=gas_limit)

        self.session.add(task)

        self.add_prior_tasks(task, prior_tasks)

        if reverses_task:
            reverses_task_obj = self.get_task_from_uuid(reverses_task)
            if reverses_task_obj:
                task.reverses = reverses_task_obj

                self.session.commit()

                # Release the multithread lock
                self.red.delete(f'MultithreadDupeLock-{reverses_task_obj.id}')

        self.session.commit()

        return task

    def create_deploy_contract_task(self,
                                    uuid: UUID,
                                    signing_wallet_obj,
                                    contract_name,
                                    args=None, kwargs=None,
                                    gas_limit=None, prior_tasks=None):

        task = BlockchainTask(uuid,
                              signing_wallet=signing_wallet_obj,
                              type='DEPLOY_CONTRACT',
                              contract_name=contract_name,
                              args=args,
                              kwargs=kwargs,
                              gas_limit=gas_limit)

        self.session.add(task)

        self.add_prior_tasks(task, prior_tasks)

        self.session.commit()

        return task

    def get_serialised_task_from_uuid(self, uuid):
        task = self.get_task_from_uuid(uuid)

        if task is None:
            return None

        base_data = {
            'id': task.id,
            'status': task.status,
            'prior_tasks': [task.uuid for task in task.prior_tasks],
            'posterior_tasks': [task.uuid for task in task.posterior_tasks],
            'transactions': [transaction.id for transaction in task.transactions]
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

    def get_duplicates(self, min_task_id, max_task_id):

        from sqlalchemy.sql import text

        query = text(
            """
                SELECT blockchain_task.id as task_id,
                  (SELECT COUNT(*)
                    FROM blockchain_transaction
                    WHERE blockchain_task_id = blockchain_task.id AND _status = 'SUCCESS'
                    ) as txn_count
                FROM blockchain_task
                RIGHT JOIN blockchain_transaction
                ON  blockchain_transaction.blockchain_task_id = blockchain_task.id
                WHERE blockchain_task.id > :min_task_id and blockchain_task.id < :max_task_id
                GROUP BY blockchain_task.id
                HAVING (
                  SELECT COUNT(*)
                  FROM blockchain_transaction
                  WHERE blockchain_task_id = blockchain_task.id AND _status = 'SUCCESS'
                  ) > 1;
            """
        )
        res = self.session.execute(query, {'min_task_id': min_task_id, 'max_task_id': max_task_id})

        duplicated_tasks = [row for row in res]
        return duplicated_tasks

    def increment_task_invokations(self, task):
        task.previous_invocations = (task.previous_invocations or 0) + 1

        self.session.commit()

    def get_task_from_uuid(self, task_uuid):
        return self.session.query(BlockchainTask).filter_by(uuid=task_uuid).first()

    def get_task_from_id(self, task_id):
        return self.session.query(BlockchainTask).get(task_id)

    def _filter_minmax_task_ids_maybe(self, query, min_task_id, max_task_id):
        if min_task_id:
            query = query.filter(BlockchainTask.id > min_task_id)
        if max_task_id:
            query = query.filter(BlockchainTask.id < max_task_id)

        return query

    def get_failed_tasks(self, min_task_id=None, max_task_id=None):
        return self._get_tasks_by_status('FAILED', min_task_id, max_task_id)

    def _get_tasks_by_status(self, status, min_task_id, max_task_id):
        query = session.query(BlockchainTask) \
            .filter(BlockchainTask.status == status) \
            .order_by(BlockchainTask.id.asc())
        query = self._filter_minmax_task_ids_maybe(query, min_task_id, max_task_id)

        return query.all()

    def get_failed_tasks(self, min_task_id=None, max_task_id=None):
        return self._get_tasks_by_status('FAILED', min_task_id, max_task_id)

    def get_pending_tasks(self, min_task_id=None, max_task_id=None):
        return self._get_tasks_by_status('PENDING', min_task_id, max_task_id)

    def get_unstarted_tasks(self, min_task_id=None, max_task_id=None):
        return self._get_tasks_by_status('UNSTARTED', min_task_id, max_task_id)

    def create_blockchain_wallet_from_encrypted_private_key(self, encrypted_private_key):

        private_key = BlockchainWallet.decrypt_private_key(encrypted_private_key)
        self.create_blockchain_wallet_from_private_key(private_key)

    def create_blockchain_wallet_from_private_key(self, private_key,
                                                  allow_existing=False,
                                                  wei_target_balance=0,
                                                  wei_topup_threshold=0,
                                                  ):

        address = BlockchainWallet.address_from_private_key(private_key)

        existing_wallet = self.session.query(BlockchainWallet).filter_by(address=address).first()
        if existing_wallet:
            if allow_existing:
                return existing_wallet
            else:
                raise WalletExistsError("Account for provided private key already exists")

        wallet = BlockchainWallet(
            private_key=private_key,
            wei_target_balance=wei_target_balance,
            wei_topup_threshold=wei_topup_threshold)

        self.session.add(wallet)

        self.session.commit()

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

        self.session.add(wallet)

        self.session.commit()

        return wallet


    def get_all_wallets(self):
        return self.session.query(BlockchainWallet).all()

    def get_wallet_by_address(self, address):
        return self.session.query(BlockchainWallet).filter(BlockchainWallet.address == address).first()

    def get_wallet_by_encrypted_private_key(self, encrypted_private_key):
         return self.session.query(BlockchainWallet).filter(
             BlockchainWallet.encrypted_private_key == encrypted_private_key).first()

    def set_wallet_last_topup_task_uuid(self, wallet_address, task_uuid):
        wallet = self.get_wallet_by_address(wallet_address)
        wallet.last_topup_task_uuid = task_uuid

        self.session.commit()

    def __init__(self, w3, red, session, PENDING_TRANSACTION_EXPIRY_SECONDS=30):

        self.w3 = w3

        self.red = red

        self.session = scoped_session(session)
        
        self.first_block_hash = w3.eth.getBlock(0).hash.hex()

        self.PENDING_TRANSACTION_EXPIRY_SECONDS = PENDING_TRANSACTION_EXPIRY_SECONDS