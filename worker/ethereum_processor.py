from abc import ABC
import json, base64, ssl
from web3 import Web3, HTTPProvider, WebsocketProvider

from ethereum import utils
from cryptography.fernet import Fernet

from celery import chain

import requests
from requests.auth import HTTPBasicAuth

from worker import celery_tasks

import config

import datetime


class PreBlockchainError(Exception):
    pass

class BaseERC20Processor(ABC):

    @staticmethod
    def send_blockchain_result_to_app(result):

        if result.get('credit_transfer_id') is None:
            print('########WARNING: No credit transfer id supplied########')

        r = requests.put(config.APP_HOST + '/api/blockchain_transaction/',
                          json=result,
                          auth=HTTPBasicAuth(config.BASIC_AUTH_USERNAME,
                                             config.BASIC_AUTH_PASSWORD))

    @staticmethod
    def claim_transaction_spot(signing_address, network_nonce):

        r = requests.post(config.APP_HOST + '/api/blockchain_transaction/',
                         json={'signing_address': signing_address,
                               'network_nonce': network_nonce},
                         auth=HTTPBasicAuth(config.BASIC_AUTH_USERNAME,
                                            config.BASIC_AUTH_PASSWORD))

        json = r.json()


        # TODO: Make more stable
        return json['nonce'], json['transaction_id']

    @staticmethod
    def decode_private_key(encoded_private_key):
        fernet_encryption_key = base64.b64encode(utils.sha3(config.SECRET_KEY))
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

    def check_for_correct_contract(self, correct_name):
        class WrongContractException(Exception):
            """Unexpected contract name"""

        found_name = self.contract.functions.name().call()
        print('Expecting Contract: ' + correct_name)
        print('Found Contract: ' + found_name)
        if found_name != correct_name:
            raise WrongContractException

        return True

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
                            credit_transfer_id=None,
                            unbuilt_transaction=None,
                            partial_txn_dict={},
                            transaction_type=None,
                            gas_limit_override=None,
                            gas_price_override=None):

        signing_address = Web3.toChecksumAddress(utils.privtoaddr(signing_private_key))

        network_nonce = self.w3.eth.getTransactionCount(signing_address, block_identifier='pending')

        nonce, transaction_id = self.claim_transaction_spot(signing_address, network_nonce)


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
            'credit_transfer_id': credit_transfer_id,
            'transaction_id': transaction_id
        }

        self.send_blockchain_result_to_app(transaction_data)

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
            sender = utils.checksum_encode(sender)

        if recipient:
            recipient = utils.checksum_encode(recipient)

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
                     http_provider,
                     websocket_provider,
                     gas_price_gwei,
                     gas_limit,):

            self.abi_dict = json.loads(contract_abi_string)
            self.contract_address = utils.checksum_encode(contract_address)
            self.ethereum_chain_id = int(ethereum_chain_id)

            self.w3 = Web3(HTTPProvider(http_provider))
            self.wsw3 = Web3(WebsocketProvider(websocket_provider))

            self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.abi_dict)
            self.decimals = self.get_decimals()

            self.gas_price = self.w3.toWei(gas_price_gwei, 'gwei')
            self.gas_limit = gas_limit
            self.transaction_max_value = self.gas_price * self.gas_limit


class MintableERC20Processor(BaseERC20Processor):

    def make_disbursement(self,
                          transfer_amount,
                          recipient_address,
                          account_to_approve_encoded_pk,
                          master_wallet_approval_status,
                          uncompleted_tasks,
                          is_retry,
                          credit_transfer_id=None):

        chain_list = [
            celery_tasks.disburse_funds.si(transfer_amount, recipient_address, credit_transfer_id),
            celery_tasks.create_transaction_response.s(credit_transfer_id)
        ]

        chain(chain_list).on_error(celery_tasks.log_error.s(credit_transfer_id)).delay()



    def make_payment(self,
                     transfer_amount,
                     sender_address,
                     recipient_address,
                     account_to_approve_encoded_pk,
                     master_wallet_approval_status,
                     uncompleted_tasks,
                     is_retry,
                     credit_transfer_id=None):

        chain_list = [
            celery_tasks.transfer_credit.si(transfer_amount, sender_address, recipient_address, credit_transfer_id),
            celery_tasks.create_transaction_response.s(credit_transfer_id),
        ]

        chain(chain_list).on_error(celery_tasks.log_error.s(credit_transfer_id)).delay()


    def make_withdrawal(self,
                        transfer_amount,
                        sender_address,
                        recipient_address,
                        account_to_approve_encoded_pk,
                        master_wallet_approval_status,
                        uncompleted_tasks,
                        is_retry,
                        credit_transfer_id=None):
        chain_list = [
            celery_tasks.make_withdrawal.si(transfer_amount, sender_address, recipient_address, credit_transfer_id),
            celery_tasks.create_transaction_response.s(credit_transfer_id),
        ]

        chain(chain_list).on_error(celery_tasks.log_error.s(credit_transfer_id)).delay()


    def disburse_funds_async(self, transfer_amount, recipient_address, credit_transfer_id):

        converted_amount = self.cents_to_native_amount(transfer_amount)

        txn = self.contract.functions.mint(recipient_address, converted_amount)

        return self.process_transaction(self.master_wallet_private_key,
                                        credit_transfer_id=credit_transfer_id,
                                        unbuilt_transaction=txn,
                                        transaction_type='initial credit mint')

    def transfer_credit_async(self,transfer_amount, sender_address, recipient_address, credit_transfer_id):

        converted_amount = self.cents_to_native_amount(transfer_amount)

        txn = self.contract.functions.transferFrom(sender_address, recipient_address, converted_amount)

        return self.process_transaction(self.master_wallet_private_key,
                                        credit_transfer_id=credit_transfer_id,
                                        unbuilt_transaction=txn,
                                        transaction_type='transfer')


    def withdrawal_async(self, transfer_amount, sender_address, recipient_address):
        return self.transfer_credit_async(transfer_amount, sender_address, recipient_address)

    def __init__(self,
                 contract_address,
                 contract_abi_string,
                 ethereum_chain_id,
                 http_provider,
                 websocket_provider,
                 gas_price_gwei,
                 gas_limit,
                 contract_owner_private_key):

        super(MintableERC20Processor, self).__init__(contract_address,
                                                     contract_abi_string,
                                                     ethereum_chain_id,
                                                     http_provider,
                                                     websocket_provider,
                                                     gas_price_gwei,
                                                     gas_limit)

        self.master_wallet_private_key = contract_owner_private_key
        self.master_wallet_address = Web3.toChecksumAddress(utils.privtoaddr(self.master_wallet_private_key))


class UnmintableERC20Processor(BaseERC20Processor):

    def make_disbursement(self,
                          transfer_amount,
                          recipient_address,
                          account_to_approve_encoded_pk,
                          master_wallet_approval_status,
                          uncompleted_tasks,
                          is_retry,
                          credit_transfer_id=None):

        chain_list = []

        approval_required = self.determine_if_master_wallet_approval_required(
            master_wallet_approval_status,
            uncompleted_tasks,
            is_retry)

        if approval_required:
            chain_list.extend(
                self.construct_master_wallet_approval_tasks(
                    account_to_approve_encoded_pk,
                    credit_transfer_id)
            )

        if not is_retry or 'disbursement' in uncompleted_tasks:
            chain_list.extend([
                celery_tasks.disburse_funds.si(transfer_amount, recipient_address, credit_transfer_id),
                celery_tasks.create_transaction_response.s(credit_transfer_id)
            ])


        if not is_retry or 'ether load' in uncompleted_tasks:
            if float(self.force_eth_disbursement_amount or 0) > 0:

                forced_amount_wei = Web3.toWei(self.force_eth_disbursement_amount, 'ether')

                chain_list.extend([
                    celery_tasks.load_ether.si(recipient_address, forced_amount_wei, 1),
                    celery_tasks.create_transaction_response.s(credit_transfer_id)
                ])

        chain(chain_list).on_error(celery_tasks.log_error.s(credit_transfer_id)).delay()

    def make_payment(self,
                     transfer_amount,
                     sender_address,
                     recipient_address,
                     account_to_approve_encoded_pk,
                     master_wallet_approval_status,
                     uncompleted_tasks,
                     is_retry,
                     credit_transfer_id=None):

        chain_list = []

        approval_required = self.determine_if_master_wallet_approval_required(
            master_wallet_approval_status,
            uncompleted_tasks,
            is_retry)

        if approval_required:
            chain_list.extend(
                self.construct_master_wallet_approval_tasks(
                    account_to_approve_encoded_pk,
                    credit_transfer_id)
            )


        if not is_retry or 'transfer' in uncompleted_tasks:
            chain_list.extend([
                celery_tasks.transfer_credit.si(transfer_amount, sender_address, recipient_address, credit_transfer_id),
                celery_tasks.create_transaction_response.s(credit_transfer_id),
            ])

        chain(chain_list).on_error(celery_tasks.log_error.s(credit_transfer_id)).delay()


    def make_withdrawal(self,
                        transfer_amount,
                        sender_address,
                        recipient_address,
                        account_to_approve_encoded_pk,
                        master_wallet_approval_status,
                        uncompleted_tasks,
                        is_retry,
                        credit_transfer_id=None):

        chain_list = []

        approval_required = self.determine_if_master_wallet_approval_required(
            master_wallet_approval_status,
            uncompleted_tasks,
            is_retry)

        if approval_required:
            chain_list.extend(
                self.construct_master_wallet_approval_tasks(
                    account_to_approve_encoded_pk,
                    credit_transfer_id)
            )

        if not is_retry or 'transfer' in uncompleted_tasks:

            chain_list.extend([
                celery_tasks.make_withdrawal.si(transfer_amount, sender_address, recipient_address, credit_transfer_id),
                celery_tasks.create_transaction_response.s(credit_transfer_id),
            ])

        chain(chain_list).on_error(celery_tasks.log_error.s(credit_transfer_id)).delay()

    def construct_master_wallet_approval_tasks(self, account_to_approve_encoded_pk, credit_transfer_id):

        private_key = self.decode_private_key(account_to_approve_encoded_pk)

        address = Web3.toChecksumAddress(utils.privtoaddr(private_key))

        gas_required, gas_price = self.estimate_load_ether_gas_and_price()

        return [
            celery_tasks.load_ether.si(address, gas_required, gas_price),
            celery_tasks.create_transaction_response.s(credit_transfer_id),
            celery_tasks.approve_master_for_transfers.si(account_to_approve_encoded_pk, gas_required, gas_price),
            celery_tasks.create_transaction_response.s(credit_transfer_id)
        ]

    def determine_if_master_wallet_approval_required(self, master_wallet_approval_status, uncompleted_tasks, is_retry):
        if master_wallet_approval_status in ['NO_REQUEST', 'FAILED'] or (
            is_retry and 'master wallet approval' in uncompleted_tasks
        ):
            # If the account hasn't received a disbursement previously,
            # it needs to approve the master wallet for transfers

            return True

        return False

    def disburse_funds_async(self, transfer_amount, recipient_address, credit_transfer_id):

        converted_amount = self.cents_to_native_amount(transfer_amount)

        fund_disbursement_txn = self.contract.functions.transfer(
            recipient_address,
            converted_amount
        )

        fund_disbursement_result = self.process_transaction(self.master_wallet_private_key,
                                                            credit_transfer_id=credit_transfer_id,
                                                            unbuilt_transaction=fund_disbursement_txn,
                                                            transaction_type='disbursement')

        return fund_disbursement_result

    def generate_approval_txn(self):

        sender_address = utils.checksum_encode(self.master_wallet_address)

        approve_amount = self.cents_to_native_amount(10 ** 8)

        transfer_approval_txn = self.contract.functions.approve(sender_address, approve_amount)

        return transfer_approval_txn

    def estimate_load_ether_gas_and_price(self):

        estimated_gas_required = round(45665 * 1.05)

        # estimated_gas_required = round(self.generate_approval_txn().estimateGas() * 1.05)

        gas_price = self.get_gas_price()

        return estimated_gas_required, gas_price


    def load_ether_async(self, recipient_address, gas_required, gas_price):

        txn_dict = {
            'to': recipient_address,
            'value': gas_required * gas_price
        }

        ether_load_result = self.process_transaction(self.master_wallet_private_key,
                                                     partial_txn_dict=txn_dict,
                                                     transaction_type='ether load')

        return ether_load_result

    def approve_master_for_transfers_async(self, account_to_approve_encoded_pk, gas_required, gas_price):

        private_key = self.decode_private_key(account_to_approve_encoded_pk)

        transfer_approval_txn = self.generate_approval_txn()

        approval_result = self.process_transaction(private_key,
                                                   unbuilt_transaction=transfer_approval_txn,
                                                   transaction_type='master wallet approval',
                                                   gas_limit_override= gas_required,
                                                   gas_price_override= gas_price
                                                   )

        return approval_result


    def transfer_credit_async(self,transfer_amount, sender_address, recipient_address, credit_transfer_id):

        converted_amount = self.zero_balance_compensated_cents_to_native_amount(transfer_amount, sender_address)

        txn = self.contract.functions.transferFrom(sender_address, recipient_address, converted_amount)

        return self.process_transaction(self.master_wallet_private_key,
                                        credit_transfer_id = credit_transfer_id,
                                        unbuilt_transaction=txn,
                                        transaction_type='transfer')

    def withdrawal_async(self,transfer_amount, sender_address, recipient_address, credit_transfer_id):

        converted_amount = self.zero_balance_compensated_cents_to_native_amount(transfer_amount, sender_address)

        if self.withdraw_to_address:
            recipient_address = self.withdraw_to_address
        else:
            recipient_address = self.master_wallet_address

        txn = self.contract.functions.transferFrom(sender_address, recipient_address, converted_amount)

        return self.process_transaction(self.master_wallet_private_key,
                                        credit_transfer_id=credit_transfer_id,
                                        unbuilt_transaction=txn,
                                        transaction_type='transfer')


    def get_master_wallet_balance_async(self):

        native_amount_balance = self.contract.functions.balanceOf(self.master_wallet_address).call()

        return self.native_amount_to_cents(native_amount_balance)

    def get_transfer_account_blockchain_addresses(self):

        r = requests.get(config.APP_HOST + '/api/blockchain_address/?filter=vendor',
                         auth=HTTPBasicAuth(config.BASIC_AUTH_USERNAME,
                                            config.BASIC_AUTH_PASSWORD))

        print('response:' + str(r))

        if r.status_code < 400:

            address_dict_list = r.json()['data']['blockchain_addresses']

            return [address_dict['address'] for address_dict in address_dict_list]
        else:
            return []


    def find_new_external_inbounds(self):

        address_list = self.get_transfer_account_blockchain_addresses()

        try:
            latest_block = self.wsw3.eth.getBlock('latest')

            threshold = latest_block.number - 2

            inbound_filter = self.websocket_contract.events.Transfer.createFilter(
                fromBlock=threshold,
                argument_filters={'dst': address_list})


            for event in inbound_filter.get_all_entries():

                try:

                    converted_amount = self.native_amount_to_cents(event['args']['wad'])

                    body = {
                        'sender_blockchain_address': event['args']['src'],
                        'recipient_blockchain_address': event['args']['dst'],
                        'blockchain_transaction_hash': event['transactionHash'].hex(),
                        'transfer_amount': converted_amount
                    }

                    r = requests.post(config.APP_HOST + '/api/credit_transfer/internal/',
                                      json=body,
                                      auth=HTTPBasicAuth(config.BASIC_AUTH_USERNAME,
                                                         config.BASIC_AUTH_PASSWORD))
                except KeyError:
                    pass

        except ssl.SSLError as e:
            pass


    def __init__(self,
                 contract_address,
                 contract_abi_string,
                 ethereum_chain_id,
                 http_provider,
                 websocket_provider,
                 gas_price_gwei,
                 gas_limit,
                 master_wallet_private_key,
                 force_eth_disbursement_amount=None,
                 withdraw_to_address = None):

        super(UnmintableERC20Processor, self).__init__(contract_address,
                                                       contract_abi_string,
                                                       ethereum_chain_id,
                                                       http_provider,
                                                       websocket_provider,
                                                       gas_price_gwei,
                                                       gas_limit)

        self.master_wallet_private_key = master_wallet_private_key
        self.master_wallet_address = Web3.toChecksumAddress(utils.privtoaddr(self.master_wallet_private_key))
        print('master wallet address: ' + self.master_wallet_address)

        self.websocket_contract = self.wsw3.eth.contract(address=self.contract_address, abi=self.abi_dict)

        self.force_eth_disbursement_amount = force_eth_disbursement_amount

        self.withdraw_to_address = withdraw_to_address
