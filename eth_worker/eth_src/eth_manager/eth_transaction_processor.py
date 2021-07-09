from typing import Optional, Any
from celery import signature
import datetime

import requests

import config
from exceptions import PreBlockchainError
from eth_manager.contract_registry.contract_registry import ContractRegistry
from celery_utils import eth_endpoint
import celery_app 
from web3.exceptions import TransactionNotFound

class EthTransactionProcessor(object):
    """
    Does the grunt work of trying to get a transaction onto an ethereum chain.
    Doesn't care about task ordering, but just reports errors if it doesn't succeed.
    Also includes call_contract_function and get wallet balance as methods due to code overlap and to keep eth
    concepts from leaking into other objects
    """

    def call_contract_function(self,
                               contract_address: str, abi_type: str, function_name: str,
                               args: Optional[tuple] = None, kwargs: Optional[dict] = None,
                               signing_address: Optional[str] = None) -> Any:
        """
        The main call entrypoint for the transaction. This task completes quickly and doesn't mutate any state, so this
        directly goes to the blockchain rather than going via the task queue.

        :param contract_address: address of the contract for the function
        :param abi_type: the type of ABI for the contract being called
        :param function_name: name of the function
        :param args: arguments for the function
        :param kwargs: keyword arguments for the function
        :param signing_address: required when the function is dependent on the signing address
        :return: the result of the contract call
        """

        args = self._shape_args(args)
        kwargs = self._shape_kwargs(kwargs)

        function_list = self.registry.get_contract_function(contract_address, function_name, abi_type)

        function = function_list(*args, **kwargs)

        txn_meta = {'gasPrice': self._get_gas_price()}

        if signing_address:
            txn_meta['from'] = signing_address

        call_data = function.call(txn_meta)

        if isinstance(call_data, bytes):
            return call_data.rstrip(b'\x00').decode()

        return call_data

    def process_send_eth_transaction(self, transaction_id,
                                     recipient_address, amount, task_id=None):

        partial_txn_dict = {
            'to': recipient_address,
            'value': amount
        }

        print(f'\n##Tx {transaction_id}, task {task_id}: Sending Eth \n'
              f'to: {recipient_address} \n'
              f'amount: {amount}')

        return self._process_transaction(transaction_id, partial_txn_dict=partial_txn_dict, gas_limit=100000)

    def process_function_transaction(self, transaction_id, contract_address, abi_type,
                                     function_name, args=None, kwargs=None, gas_limit=None, task_id=None):

        args = self._shape_args(args)
        kwargs = self._shape_kwargs(kwargs)

        print(f'\n##Tx {transaction_id}, task {task_id}: Transacting with Function {function_name} \n'
              f'Args: {args} \n'
              f'Kwargs: {kwargs}')

        fn = self.registry.get_contract_function(contract_address, function_name, abi_type)

        bound_function = fn(*args, **kwargs)

        return self._process_transaction(transaction_id, unbuilt_transaction=bound_function, gas_limit=gas_limit)

    def process_deploy_contract_transaction(self, transaction_id, contract_name,
                                            args=None, kwargs=None, gas_limit=None, task_id=None):

        args = self._shape_args(args)
        kwargs = self._shape_kwargs(kwargs)

        print(f'\n##Tx {transaction_id}, task {task_id}: Deploying Contract {contract_name} \n'
              f'Args: {args} \n'
              f'Kwargs: {kwargs}')

        contract = self.registry.get_compiled_contract(contract_name)

        constructor = contract.constructor(*args, **kwargs)

        return self._process_transaction(transaction_id, unbuilt_transaction=constructor, gas_limit=gas_limit)

    def _process_transaction(self,
                             transaction_id,
                             unbuilt_transaction=None,
                             partial_txn_dict=None,
                             gas_limit=None,
                             gas_price=None):

        signing_wallet_obj = self.persistence.get_transaction_signing_wallet(transaction_id)

        metadata = self._compile_transaction_metadata(
            signing_wallet_obj,
            transaction_id,
            unbuilt_transaction,
            gas_limit,
            gas_price
        )

        built_txn = self._construct_full_txn_dict(
            metadata,
            partial_txn_dict,
            unbuilt_transaction
        )

        signed_transaction = self.w3.eth.account.sign_transaction(
            built_txn,
            private_key=signing_wallet_obj.private_key
        )

        # Save the hash and nonce before attempting txn
        self.persistence.update_transaction_data(
            transaction_id,
            {
                'hash': signed_transaction.hash.hex(),
                'nonce': metadata['nonce'],
            }
        )

        self._send_signed_transaction(signed_transaction, transaction_id)


        # If we've made it this far, the nonce will(?) be consumed
        self.persistence.update_transaction_data(
            transaction_id,
            {
                'submitted_date': str(datetime.datetime.utcnow()),
                'nonce_consumed': True
            }
        )

        return transaction_id

    def _calculate_nonce(self, signing_wallet_obj, transaction_id):
        network_nonce = self.w3.eth.getTransactionCount(signing_wallet_obj.address, block_identifier='pending')

        return self.persistence.locked_claim_transaction_nonce(
            network_nonce, signing_wallet_obj.id, transaction_id
        )

    def _compile_transaction_metadata(
            self,
            signing_wallet_obj,
            transaction_id,
            unbuilt_transaction=None,
            gas_limit=None,
            gas_price=None):

        chain_id = self.ethereum_chain_id
        gas_price = gas_price or self.gas_price_wei

        if gas_limit:
            gas = gas_limit
        else:
            if not unbuilt_transaction:
                raise Exception("Must specify gas limit or an unbuilt transaction")
            try:
                gas = unbuilt_transaction.estimateGas({
                    'from': signing_wallet_obj.address,
                    'gasPrice': gas_price
                })
            except ValueError as e:
                print("Estimate Gas Failed. Remedy by specifying gas limit.")

                raise e

        nonce = self.w3.eth.getTransactionCount(signing_wallet_obj.address, block_identifier='pending')
        metadata = {
            'gas': gas,
            'gasPrice': gas_price,
            'nonce': nonce
        }
        if chain_id:
            metadata['chainId'] = chain_id

        return metadata

    def _construct_full_txn_dict(self, metadata, partial_txn_dict=None, unbuilt_transaction=None):

        if not partial_txn_dict and not unbuilt_transaction:
            raise Exception("Must provide partial_txn_dict and/or unbuilt_transaction data")

        if not partial_txn_dict:
            partial_txn_dict = {}

        txn_dict = {**metadata, **partial_txn_dict}

        if unbuilt_transaction:
            txn_dict =  unbuilt_transaction.buildTransaction(txn_dict)

        return txn_dict

    def _send_signed_transaction(self, signed_transaction, transaction_id):
        try:

            self.w3.eth.sendRawTransaction(signed_transaction.rawTransaction)

        except ValueError as e:
            message = f'Transaction {transaction_id}: {str(e)}'
            raise PreBlockchainError(message)

    def _get_gas_price(self, target_transaction_time=None):

        if not target_transaction_time:
            target_transaction_time = celery_app.chain_config['TARGET_TRANSACTION_TIME']

        try:
            gas_price_req = requests.get(celery_app.chain_config['GAS_PRICE_PROVIDER'] + '/price',
                                         params={'max_wait_seconds': target_transaction_time}).json()

            gas_price = min(gas_price_req['gas_price'], self.gas_price_wei)

            print('gas price: {}'.format(gas_price))

        except Exception as e:
            gas_price = self.gas_price_wei

        return gas_price

    def get_transaction_status(self, transaction_id):
        transaction_object = self.persistence.get_transaction(transaction_id)
        transaction_hash = transaction_object.hash

        return self._status_from_hash(transaction_hash)

    def _status_from_hash(self, transaction_hash):

        print('watching txn: {} at {}'.format(transaction_hash, datetime.datetime.utcnow()))

        if not transaction_hash:
            return {
               'status': 'FAILED',
               'error': 'No Transaction Hash Provided',
            }

        try:
            tx_receipt = self.w3.eth.getTransactionReceipt(transaction_hash)
        except TransactionNotFound:
            tx_receipt = None

        if tx_receipt is None:
            return {'status': 'PENDING'}

        mined_date = str(datetime.datetime.utcnow())

        if tx_receipt.blockNumber is None:
            return {'status': 'PENDING', 'message': 'Next Block'}

        if tx_receipt.status == 1:

            return {
                'status': 'SUCCESS',
                'block': tx_receipt.blockNumber,
                'contract_address': tx_receipt.contractAddress,
                'mined_date': mined_date
            }

        else:

           return {
               'status': 'FAILED',
               'error': 'Blockchain Error',
               'block': tx_receipt.blockNumber,
               'mined_date': mined_date
           }


    def _shape_args(self, args):
        args = args or tuple()
        if not isinstance(args, (list, tuple)):
            args = [args]
        return [self._typecast_argument(a) for a in args]

    def _shape_kwargs(self, kwargs):
        kwargs = kwargs or dict()
        return {k: self._typecast_argument(v) for k, v in kwargs.items()}

    def _typecast_argument(self, argument):
        if isinstance(argument, dict) and argument.get('type') == 'bytes':
            return argument.get('data').encode()
        return argument

    def get_wallet_balance(self, wallet):
        return self.w3.eth.getBalance(wallet.address)

    def __init__(
            self,
            ethereum_chain_id,
            w3,
            gas_price_wei,
            gas_limit,
            persistence
    ):

        self.registry = ContractRegistry(w3)
        self.ethereum_chain_id = int(ethereum_chain_id) if ethereum_chain_id else None
        self.w3 = w3
        self.gas_price_wei = gas_price_wei
        self.gas_limit = gas_limit
        self.persistence = persistence
        self.sigs = SigGenerators()


class SigGenerators(object):

    def process_send_eth_transaction(
            self,
            transaction_id,
            recipient_address,
            transfer_amount,
            task_id
    ):
        return signature(
            eth_endpoint('_process_send_eth_transaction'),
            args=(
                transaction_id,
                recipient_address,
                transfer_amount,
                task_id
            )
        )

    def process_function_transaction(
            self,
            transaction_id,
            contract_address,
            abi_type,
            fn,
            args,
            kwargs,
            gas_limit,
            task_id
    ):
        return signature(
            eth_endpoint('_process_function_transaction'),
            args=(
                transaction_id,
                contract_address,
                abi_type,
                fn,
                args,
                kwargs,
                gas_limit,
                task_id
            )
        )

    def process_deploy_contract_transaction(
            self,
            transaction_id,
            contract_name,
            args,
            kwargs,
            gas_limit,
            task_id
    ):
        return signature(
            eth_endpoint('_process_deploy_contract_transaction'),
            args=(
                transaction_id,
                contract_name,
                args,
                kwargs,
                gas_limit,
                task_id
            )
        )

    def call_contract_function(self, contract_address, contract_type, func, args=None):
        return signature(
            eth_endpoint('call_contract_function'),
            kwargs={
                'contract_address': contract_address,
                'abi_type': contract_type,
                'function': func,
                'args': args,
            }
        )


