import datetime
from typing import Tuple
from sqlalchemy import and_, or_
from sqlalchemy.sql import func

from sempo_types import UUID, UUIDList

from celery_utils import chain
import config

from sql_persistence.models import (
    BlockchainTransaction,
    BlockchainTask,
    BlockchainWallet,
    SynchronizedBlock,
    SynchronizationFilter
)

from exceptions import (
    WalletExistsError
)

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

    def locked_claim_transaction_nonce(
            self,
            network_nonce,
            signing_wallet_id: int,
            transaction_id: int
    ) -> int:
        """
        Claim a transaction a nonce for a particular transaction, using a lock to prevent another transaction
        from accidentially claiming the same nonce.

        :param network_nonce: the highest nonce that we know has been claimed on chain
        :param signing_wallet_id: the wallet object that will be used to sign the transaction
        :param transaction_id: the id of the transaction object
        :return: a tuple of the claimed nonce, and the transaction_id (transaction_id is passed through for chaining)
        """

        signing_wallet = self.session.query(BlockchainWallet).get(signing_wallet_id)
        transaction = self.session.query(BlockchainTransaction).get(transaction_id)

        lock = self.red.lock(signing_wallet.address, timeout=600)
        print(f'Attempting lock for txn: {transaction_id} \n'
              f'addr:{signing_wallet.address}')
        # Commits here are because the database would sometimes timeout during a long lock
        # and could not cleanly restart with uncommitted data in the session. Committing before
        # the lock, and then once it's reclaimed lets the session gracefully refresh if it has to.
        self.session.commit()
        with lock:
            self.session.commit()
            self.session.refresh(signing_wallet)

            nonce = self._claim_transaction_nonce(network_nonce, signing_wallet, transaction)
            return nonce

    def _claim_transaction_nonce(
            self,
            network_nonce: int,
            signing_wallet: BlockchainWallet,
            transaction: BlockchainTransaction,
    ) -> int:

        if transaction.nonce is not None:
            return transaction.nonce
        calculated_nonce = self._calculate_nonce(signing_wallet, network_nonce)
        transaction.signing_wallet = signing_wallet
        transaction.nonce = calculated_nonce
        transaction.status = 'PENDING'

        # TODO: can we shift this commit out?
        self.session.commit()

        return calculated_nonce

    def update_transaction_data(self, transaction_id, transaction_data):
        transaction = self.session.query(BlockchainTransaction).get(transaction_id)

        for attribute in transaction_data:
            if transaction_data[attribute] != getattr(transaction, attribute):
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
            # TODO: when is this ever not the case?
            # We should just force signing walelt based off the task
            blockchain_transaction.task = task

        self.session.commit()

        return blockchain_transaction

    # Gets transaction using transaction_id OR hash
    def get_transaction(self, transaction_id = None, hash = None):
        if transaction_id:
            return self.session.query(BlockchainTransaction).get(transaction_id)
        else:
            return self.session.query(BlockchainTransaction).filter_by(hash=hash).first()
    
    def get_transaction_signing_wallet(self, transaction_id):

        transaction = self.session.query(BlockchainTransaction).get(transaction_id)

        return transaction.signing_wallet

    def set_task_status_text(self, task, text):
        task.status_text = text
        self.session.commit()

    def create_send_eth_task(self,
                             uuid: UUID,
                             signing_wallet_obj,
                             recipient_address, amount_wei,
                             prior_tasks=None,
                             posterior_tasks=None):

        task = BlockchainTask(uuid,
                              signing_wallet=signing_wallet_obj,
                              type='SEND_ETH',
                              is_send_eth=True,
                              recipient_address=recipient_address,
                              amount=amount_wei,
                              prior_tasks=prior_tasks,
                              posterior_tasks=posterior_tasks)

        self.session.add(task)
        self.session.commit()

        return task

    def create_deploy_contract_task(self,
                                    uuid: UUID,
                                    signing_wallet_obj,
                                    contract_name,
                                    args=None, kwargs=None,
                                    gas_limit=None,
                                    prior_tasks=None, posterior_tasks=None):

        task = BlockchainTask(uuid,
                              signing_wallet=signing_wallet_obj,
                              type='DEPLOY_CONTRACT',
                              contract_name=contract_name,
                              args=args,
                              kwargs=kwargs,
                              gas_limit=gas_limit,
                              prior_tasks=prior_tasks,
                              posterior_tasks=posterior_tasks)

        self.session.add(task)
        self.session.commit()

        return task

    def create_function_task(self,
                             uuid: UUID,
                             signing_wallet_obj,
                             contract_address, abi_type,
                             function_name, args=None, kwargs=None,
                             gas_limit=None,
                             prior_tasks=None, posterior_tasks=None,
                             reverses_task=None):


        task = BlockchainTask(uuid,
                              signing_wallet=signing_wallet_obj,
                              type='FUNCTION',
                              contract_address=contract_address,
                              abi_type=abi_type,
                              function=function_name,
                              args=args,
                              kwargs=kwargs,
                              gas_limit=gas_limit,
                              prior_tasks=prior_tasks,
                              posterior_tasks=posterior_tasks)

        self.session.add(task)

        if reverses_task:
            reverses_task_obj = self.get_task_from_uuid(reverses_task)
            if reverses_task_obj:
                task.reverses = reverses_task_obj

                self.session.commit()

                # Release the multithread lock
                self.red.delete(f'MultithreadDupeLock-{reverses_task_obj.id}')

        self.session.commit()

        return task

    def remove_prior_task_dependency(self, task_uuid: UUID, prior_task_uuid: UUID):

        task = self.get_task_from_uuid(task_uuid=task_uuid)
        prior_task = self.get_task_from_uuid(task_uuid=prior_task_uuid)
        if task and prior_task:
            try:
                task.prior_tasks.remove(prior_task)
                self.session.commit()
            except ValueError:
                pass

    def remove_all_posterior_dependencies(self, prior_task_uuid: UUID) -> UUIDList:
        prior_task = self.get_task_from_uuid(task_uuid=prior_task_uuid)

        posterior_task_uuids = [t.uuid for t in prior_task.posterior_tasks]

        prior_task.posterior_tasks = []

        self.session.commit()

        return posterior_task_uuids

    def increment_task_invocations(self, task_uuid: UUID):

        task = self.get_task_from_uuid(task_uuid=task_uuid)
        if task:
            task.previous_invocations = (task.previous_invocations or 0) + 1
            self.session.commit()

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

    def _get_tasks_by_status(self, status, min_task_id, max_task_id):
        query = self.session.query(BlockchainTask) \
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

    def get_unstarted_posteriors(self, task_uuid):

        task = self.get_task_from_uuid(task_uuid=task_uuid)

        if not task:
            return None

        if task:
            unstarted_posteriors = []
            for posterior in task.posterior_tasks:
                if posterior.status == 'UNSTARTED':
                    unstarted_posteriors.append(posterior)

            return unstarted_posteriors

    def get_unsatisfied_prior_tasks(self, task_uuid):

        task = self.get_task_from_uuid(task_uuid=task_uuid)

        if not task:
            return None

        unsatisfied = []
        for prior in task.prior_tasks:
            if prior.status != 'SUCCESS':
                unsatisfied.append(prior)

        return unsatisfied

    def get_signing_wallet_object(self, signing_address, encrypted_private_key):
        if signing_address:

            signing_wallet_obj = self.get_wallet_by_address(signing_address)

            if signing_wallet_obj is None:
                raise Exception('Address {} not found'.format(signing_address))

        elif encrypted_private_key:

            signing_wallet_obj = self.get_wallet_by_encrypted_private_key(encrypted_private_key)

            if not signing_wallet_obj:
                signing_wallet_obj = self.create_blockchain_wallet_from_encrypted_private_key(
                    encrypted_private_key=encrypted_private_key
                )
        else:
            raise Exception("Must provide encrypted private key")

        return signing_wallet_obj


    def create_blockchain_wallet_from_encrypted_private_key(self, encrypted_private_key):

        private_key = BlockchainWallet.decrypt_private_key(encrypted_private_key)
        return self.create_blockchain_wallet_from_private_key(private_key)

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

    def create_external_transaction(self, status, block, hash, contract_address, is_synchronized_with_app, recipient_address, sender_address, amount):
        transaction_object = BlockchainTransaction(
            _status = status,
            block = block,
            hash = hash,
            contract_address = contract_address,
            is_synchronized_with_app = is_synchronized_with_app,
            recipient_address = recipient_address,
            sender_address = sender_address,
            amount = amount,
            is_third_party_transaction = True # External transaction will always be third party
        )   
        self.session.add(transaction_object)
        self.session.commit()
        return transaction_object

    def mark_transaction_as_completed(self, transaction):
        transaction.is_synchronized_with_app = True
        self.session.commit()
        return transaction

    def get_transaction_by_hash(self, hash):
        return self.session.query(BlockchainTransaction).filter(BlockchainTransaction.hash == hash).first()

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

    def check_if_synchronization_filter_exists(self, contract_address, filter_parameters):
        filter = self.session.query(SynchronizationFilter).filter(
            SynchronizationFilter.contract_address == contract_address, SynchronizationFilter.filter_parameters == filter_parameters).first()
        if filter == None:
            return False
        return filter

    def get_transaction_sync_metrics(self):
        def __query_tuple_list_to_dict__(result):
            return { key: value for (key, value) in result }

        unsynchronized_transaction_count = self.session.query(
            BlockchainTransaction.contract_address, func.count(BlockchainTransaction.id))\
            .group_by(BlockchainTransaction.contract_address)\
            .filter(BlockchainTransaction.is_synchronized_with_app == False)\
            .all()

        synchronized_transaction_count = self.session.query(
            BlockchainTransaction.contract_address, func.count(BlockchainTransaction.id))\
            .group_by(BlockchainTransaction.contract_address)\
            .filter(BlockchainTransaction.is_synchronized_with_app == True)\
            .all()

        unsynchronized_block_count = self.session.query(
            SynchronizationFilter.contract_address, func.count(SynchronizedBlock.id))\
            .group_by(SynchronizationFilter.contract_address)\
            .filter(SynchronizedBlock.status != 'SUCCESS')\
            .join(SynchronizationFilter)\
            .all()

        synchronized_block_count = self.session.query(
            SynchronizationFilter.contract_address, func.count(SynchronizedBlock.id))\
            .group_by(SynchronizationFilter.contract_address)\
            .filter(SynchronizedBlock.status == 'SUCCESS')\
            .join(SynchronizationFilter)\
            .all()

        max_synchronized_blocks = self.session.query(SynchronizationFilter.contract_address, SynchronizationFilter.max_block).all()
        
        last_time_synchronized = self.session.query(SynchronizationFilter.contract_address, SynchronizationFilter.updated).all()

        return {
            'unsynchronized_transaction_count': __query_tuple_list_to_dict__(unsynchronized_transaction_count),
            'synchronized_transaction_count': __query_tuple_list_to_dict__(synchronized_transaction_count),
            'unsynchronized_block_count': __query_tuple_list_to_dict__(unsynchronized_block_count),
            'synchronized_block_count': __query_tuple_list_to_dict__(synchronized_block_count),
            'max_synchronized_blocks': __query_tuple_list_to_dict__(max_synchronized_blocks),
            'last_time_synchronized': __query_tuple_list_to_dict__(last_time_synchronized)
        }
        
    # Utility function for get_failed_block_fetches and get_failed_callbacks
    def __aggregate_tuple_list__(self, response):
        result = {}
        for address, hash in response:
            if hash:
                if address in result:
                    result[address].append(hash)
                else:
                    result[address] = [hash]
        return result

    def get_failed_block_fetches(self):
        failed_block_fetches = self.session.query(
            SynchronizationFilter.contract_address, SynchronizedBlock.block_number)\
            .filter(SynchronizedBlock.status != 'SUCCESS')\
            .join(SynchronizationFilter)\
            .all()
        return self.__aggregate_tuple_list__(failed_block_fetches)

    def get_failed_callbacks(self):
        failed_callbacks = self.session.query(
            BlockchainTransaction.contract_address, BlockchainTransaction.hash)\
            .filter(BlockchainTransaction.is_synchronized_with_app == False)\
            .all()
        return self.__aggregate_tuple_list__(failed_callbacks)

    def add_transaction_filter(self, contract_address, contract_type, filter_parameters, filter_type, decimals, block_epoch):
        filter = SynchronizationFilter(contract_address=contract_address, contract_type=contract_type, filter_parameters=filter_parameters, max_block=block_epoch, filter_type=filter_type, decimals=decimals)
        self.session.add(filter)
        self.session.commit()
        return filter

    def set_filter_max_block(self, filter_id, block):
        filter = self.session.query(SynchronizationFilter).filter(SynchronizationFilter.id == filter_id).first()
        filter.max_block = block
        self.session.commit()
        return True

    def get_synchronization_filter_by_id(self, filter_id):
        return self.session.query(SynchronizationFilter).filter(SynchronizationFilter.id == filter_id).first()

    def get_synchronization_filter_by_address(self, address):
        return self.session.query(SynchronizationFilter).filter(SynchronizationFilter.contract_address == address).first()

    def get_all_synchronization_filters(self):
        return self.session.query(SynchronizationFilter).all()

    def add_block_range(self, start, end, filter_id):
        for n in range(start, end + 1):
            block = SynchronizedBlock(
                block_number=n,
                status='PENDING',
                is_synchronized=False,
                synchronization_filter_id=filter_id
            )
            self.session.add(block)
        self.session.commit()

    def set_block_range_status(self, start, end, status, filter_id):
        self.session.query(SynchronizedBlock).filter(
            SynchronizedBlock.block_number >= start,
            SynchronizedBlock.block_number <= end,
            SynchronizedBlock.synchronization_filter_id == filter_id
        ).update({'status': status})

        self.session.commit()


    def __init__(self, red, session, first_block_hash, PENDING_TRANSACTION_EXPIRY_SECONDS=config.CHAINS[chain]['PENDING_TRANSACTION_EXPIRY_SECONDS']):
        self.red = red

        self.session = session
        
        self.first_block_hash = first_block_hash

        self.PENDING_TRANSACTION_EXPIRY_SECONDS = PENDING_TRANSACTION_EXPIRY_SECONDS
