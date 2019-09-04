import json, base64, ssl, datetime, random, time

from sqlalchemy import (
    or_,
    and_
)

from web3 import (
    Web3,
    HTTPProvider,
    WebsocketProvider,
    eth
)

from eth_keys import keys
from eth_utils import keccak, to_checksum_address

from cryptography.fernet import Fernet

from celery import chain

import requests
from requests.auth import HTTPBasicAuth

from eth_worker import celery_tasks
from eth_worker.models import BlockchainTransaction, session

import config


class PreBlockchainError(Exception):
    """Error before transaction sent to blockchain"""

class WrongContractNameError(Exception):
    """Unexpected contract name"""

class SQLAlchemyDataStore(object):

    def fail_expired_transactions(self):
        expire_time = datetime.datetime.utcnow() - datetime.timedelta(
            seconds=self.PENDING_TRANSACTION_EXPIRY_SECONDS
        )

        (session.query(BlockchainTransaction)
         .filter(and_(BlockchainTransaction.status == 'PENDING',
                      BlockchainTransaction.created > expire_time))
         .update({BlockchainTransaction.status: 'FAILED'}, synchronize_session=False))

    def calculate_nonce(self, singing_address, starting_nonce=0):

        self.fail_expired_transactions()

        successful_or_pending = (session.query(BlockchainTransaction)
                                 .filter(BlockchainTransaction.signing_address == singing_address)
                                 .filter(or_(BlockchainTransaction.status == 'SUCCESS',
                                             BlockchainTransaction.status == 'PENDING'))
                                 .filter(BlockchainTransaction.nonce >= starting_nonce)
                                 .order_by(BlockchainTransaction.nonce.asc())
                                 .all())

        nonce_set = set()

        for txn in successful_or_pending:
            nonce_set.add(txn.nonce)

        next_nonce = starting_nonce
        while next_nonce in nonce_set:
            next_nonce += 1

        return next_nonce

    def claim_transaction_nonce(self, signing_address):

        network_nonce = self.w3.eth.getTransactionCount(signing_address, block_identifier='pending')

        calculated_nonce = self.calculate_nonce(signing_address)

        blockchain_transaction = BlockchainTransaction(status='PENDING',
                                                       nonce=calculated_nonce,
                                                       signing_address=signing_address)

        session.add(blockchain_transaction)
        session.commit()

        gauranteed_clash_free = False

        clash_fix_attempts = 0
        while not gauranteed_clash_free and clash_fix_attempts < 200:
            clash_fix_attempts += 1
            # Occasionally two workers will hit the db at the same time and claim the same nonce

            clashed_nonces = (session.query(BlockchainTransaction)
                              .filter(BlockchainTransaction.signing_address == signing_address)
                              .filter(BlockchainTransaction.status == 'PENDING')
                              .filter(BlockchainTransaction.nonce == blockchain_transaction.nonce)
                              .all())

            if len(clashed_nonces) > 1:
                # If there is a clash, just try again
                print('~~~~~~~~~~~~~~~~~~~fixing clash~~~~~~~~~~~~~~~~~~~')

                # Sleeping the process by a small random amount to force the two processes out of lockstep
                time_to_sleep = random.random() / 100
                time.sleep(time_to_sleep)

                calculated_nonce = self.calculate_nonce(signing_address, network_nonce)
                blockchain_transaction.nonce = calculated_nonce

                session.commit()

            else:
                gauranteed_clash_free = True

        return calculated_nonce, blockchain_transaction.id

    def update_transaction_data(self, transaction_id, transaction_data):

        transaction = session.query(BlockchainTransaction).get(transaction_id)

        for attribute in transaction_data:
            setattr(transaction, attribute, transaction_data[attribute])

        session.commit()

    def __init__(self, w3, PENDING_TRANSACTION_EXPIRY_SECONDS=300):

        self.w3 = w3

        self.PENDING_TRANSACTION_EXPIRY_SECONDS = PENDING_TRANSACTION_EXPIRY_SECONDS

class ContractRegistry(object):

    def _get_contract_name(self, contract):
        bytes_contract_name = contract.functions.name().call()
        null_byte_stripped_name = bytes(filter(None,bytes_contract_name))
        return null_byte_stripped_name.decode()

    def _check_contract_name(self, contract_name, expected_name):

        print('Expecting Contract: ' + expected_name)
        print('Found Contract: ' + contract_name)
        if contract_name != expected_name:
            raise WrongContractNameError

    def register_contract(self, contract_address, abi, contract_name=None, require_name_matches_contract = False):
        checksum_address = to_checksum_address(contract_address)

        contract = self.w3.eth.contract(address=checksum_address, abi=abi)

        found_contract_name = self._get_contract_name(contract)

        if require_name_matches_contract:
            self._check_contract_name(found_contract_name, contract_name)

        if contract_name in self.contracts:
            raise Exception("Contract with name {} already registered".format(contract_name))

        self.contracts[contract_name] = contract

    def get_contract_function(self, contract_name, function_name):
        contract = self.contracts[contract_name]
        return getattr(contract.functions, function_name)

    def __init__(self, w3):

        self.w3 = w3
        self.contracts = {}


class TransactionProcessor(object):
    @staticmethod
    def decode_private_key(encoded_private_key):
        fernet_encryption_key = base64.b64encode(keccak(text=config.SECRET_KEY))
        cipher_suite = Fernet(fernet_encryption_key)

        return cipher_suite.decrypt(encoded_private_key.encode('utf-8')).decode('utf-8')

    def get_decimals(self):
        return self.contract.functions.decimals().call()

    def cents_to_native_amount(self, cents):
        # dividing by 100 because we work in cents
        return int(float(cents) * (10**self.decimals) / 100 / config.INTERNAL_TO_TOKEN_RATIO)

    def zero_balance_compensated_cents_to_native_amount(self, cents, sender_address):

        requested_native_amount = self.cents_to_native_amount(cents)

        sender_balance = self.contract.functions.balanceOf(sender_address).call()

        if abs(requested_native_amount - sender_balance) < 1e10:
            print('Requested amount {} is close to balance {}, using balanace instead'.format(
                requested_native_amount, sender_balance
            ))
            return sender_balance

        return requested_native_amount

    def native_amount_to_cents(self, native_amount):
        return int(int(native_amount) / (10**self.decimals) * 100 * config.INTERNAL_TO_TOKEN_RATIO)


    def check_if_valid_address(self,address):
        return Web3.isAddress(address)

    def get_gas_price(self, target_transaction_time=None):

        if not target_transaction_time:
            target_transaction_time = config.ETH_TARGET_TRANSACTION_TIME

        try:
            gas_price_req = requests.get(config.ETH_GAS_PRICE_PROVIDER + '/price',
                                         params={'max_wait_seconds': target_transaction_time}).json()

            gas_price = min(gas_price_req['gas_price'], self.gas_price)

            print('gas price: {}'.format(gas_price))

        except Exception as e:
            gas_price = self.gas_price

        return gas_price

    def process_transaction(self,
                            signing_private_key,
                            unbuilt_transaction=None,
                            partial_txn_dict={},
                            transaction_type=None,
                            gas_limit_override=None,
                            gas_price_override=None):

        signing_address = keys.PrivateKey(signing_private_key).public_key.to_checksum_address()

        nonce, transaction_id = self.persistence_model.claim_transaction_nonce(signing_address)

        print('@@@@@@@@@@@@@@ using nonce @@@@@@@@@@@@@@: {}'.format(nonce))

        txn = {
            'chainId': self.ethereum_chain_id,
            'gas': gas_limit_override or self.gas_limit,
            'gasPrice': gas_price_override or self.get_gas_price(),
            'nonce': nonce
        }

        if unbuilt_transaction:
            txn = unbuilt_transaction.buildTransaction(txn)
        else:
            txn = {**txn, **partial_txn_dict}

        signed_txn = self.w3.eth.account.signTransaction(txn, private_key=signing_private_key)

        transaction_data = {
            'transaction_hash': signed_txn.hash.hex(),
            'transaction_nonce': nonce,
            'transaction_type': transaction_type,
            'signing_address': signing_address,
            'submitted_date': str(datetime.datetime.utcnow()),
            'transaction_id': transaction_id
        }


        try:
            result = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)

        except ValueError as e:

            transaction_data['status'] = 'FAILED'
            transaction_data['message'] = str(e)

            raise PreBlockchainError(transaction_data)

        print('*****************transaction_data:*****************')
        print(transaction_data)

        return transaction_data

    def create_transaction_response(self, tx_hash):

        print('watching txn: {} at {}'.format(tx_hash, datetime.datetime.utcnow()))

        tx_receipt = self.w3.eth.getTransactionReceipt(tx_hash)

        def print_and_return(return_dict):
            print('{} for txn: {}'.format(return_dict.get('status'),tx_hash))
            return return_dict

        if tx_receipt is None:
            return print_and_return({'status': 'PENDING'})

        added_date = str(datetime.datetime.utcnow())

        if tx_receipt.blockNumber is None:
            return print_and_return({'status': 'PENDING', 'message': 'Next Block'})

        if tx_receipt.status == 1:

            return print_and_return({'status': 'SUCCESS',
                                      'block': tx_receipt.blockNumber,
                                      'added_date': added_date})

        else:
           return print_and_return({'status': 'FAILED',
                                    'message': 'Error on blockchain',
                                    'block': tx_receipt.blockNumber,
                                    'added_date': added_date})

    def make_disbursement(self,
                          transfer_amount,
                          recipient_address,
                          account_to_approve_encoded_pk,
                          master_wallet_approval_status,
                          uncompleted_tasks,
                          is_retry,
                          credit_transfer_id=None):
        pass

    def make_payment(self,
                     transfer_amount,
                     sender_address,
                     recipient_address,
                     account_to_approve_encoded_pk,
                     master_wallet_approval_status,
                     uncompleted_tasks,
                     is_retry,
                     credit_transfer_id=None,):
        pass

    def make_withdrawal(self,
                        transfer_amount,
                        sender_address,
                        recipient_address,
                        account_to_approve_encoded_pk,
                        master_wallet_approval_status,
                        uncompleted_tasks,
                        is_retry,
                        credit_transfer_id=None):
        pass

    def parse_blockchain_task(self, task):

        print('-----------------------------------------------------------------')
        print('{} parsing task:'.format(datetime.datetime.utcnow()))
        print(task)

        type = task.get('type')
        transfer_amount = task.get('transfer_amount')
        sender = task.get('sender')
        recipient = task.get('recipient')
        account_to_approve_encoded_pk = task.get('account_to_approve_pk')
        credit_transfer_id = task.get('credit_transfer_id')
        master_wallet_approval_status = task.get('master_wallet_approval_status')
        uncompleted_tasks = task.get('uncompleted_tasks')
        is_retry = task.get('is_retry')

        if sender:
            sender = to_checksum_address(sender)

        if recipient:
            recipient = to_checksum_address(recipient)

        if type == 'DISBURSEMENT':
            self.make_disbursement(transfer_amount=transfer_amount,
                                   recipient_address=recipient,
                                   account_to_approve_encoded_pk=account_to_approve_encoded_pk,
                                   master_wallet_approval_status=master_wallet_approval_status,
                                   uncompleted_tasks=uncompleted_tasks,
                                   is_retry=is_retry,
                                   credit_transfer_id=credit_transfer_id)

        elif type == 'WITHDRAWAL':

            self.make_withdrawal(transfer_amount=transfer_amount,
                                 sender_address=sender,
                                 recipient_address=recipient,
                                 account_to_approve_encoded_pk=account_to_approve_encoded_pk,
                                 master_wallet_approval_status=master_wallet_approval_status,
                                 uncompleted_tasks=uncompleted_tasks,
                                 is_retry=is_retry,
                                 credit_transfer_id=credit_transfer_id)


        else:

            self.make_payment(transfer_amount=transfer_amount,
                              sender_address=sender,
                              recipient_address=recipient,
                              account_to_approve_encoded_pk=account_to_approve_encoded_pk,
                              master_wallet_approval_status=master_wallet_approval_status,
                              uncompleted_tasks=uncompleted_tasks,
                              is_retry=is_retry,
                              credit_transfer_id=credit_transfer_id)

    def __init__(self,
                 contract_address,
                 contract_abi_string,
                 ethereum_chain_id,
                 w3,
                 gas_price_gwei,
                 gas_limit,
                 persistence_model = SQLAlchemyDataStore):

            self.abi_dict = json.loads(contract_abi_string)
            self.contract_address = to_checksum_address(contract_address)
            self.ethereum_chain_id = int(ethereum_chain_id)

            self.w3 = w3

            self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.abi_dict)
            self.decimals = self.get_decimals()

            self.gas_price = self.w3.toWei(gas_price_gwei, 'gwei')
            self.gas_limit = gas_limit
            self.transaction_max_value = self.gas_price * self.gas_limit

            self.persistence_model = persistence_model(self.w3)

