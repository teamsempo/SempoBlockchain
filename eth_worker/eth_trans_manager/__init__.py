# https://stackoverflow.com/questions/54617308/pip-install-produces-the-following-error-on-mac-error-command-gcc-failed-wit
# python3.7 / concurrent / futures/thread.py line 135 was originally self._work_queue = queue.SimpleQueue()

from celery import Celery
from raven import Client
import redis

from web3 import (
    Web3,
    WebsocketProvider,
    HTTPProvider
)

import config
from eth_trans_manager.ABIs import dai_abi
from eth_trans_manager.processor import TransactionProcessor, ContractRegistry

ERC20_config = {}
ERC20_config['ethereum_chain_id'] = config.ETH_CHAIN_ID
# ERC20_config['http_provider'] = config.ETH_HTTP_PROVIDER
ERC20_config['gas_price_gwei'] = config.ETH_GAS_PRICE
ERC20_config['gas_limit'] = config.ETH_GAS_LIMIT
ERC20_config['w3'] = Web3(HTTPProvider(config.ETH_HTTP_PROVIDER))

ETH_CHECK_TRANSACTION_RETRIES = config.ETH_CHECK_TRANSACTION_RETRIES
ETH_CHECK_TRANSACTION_RETRIES_TIME_LIMIT = config.ETH_CHECK_TRANSACTION_RETRIES_TIME_LIMIT
ETH_CHECK_TRANSACTION_BASE_TIME = config.ETH_CHECK_TRANSACTION_BASE_TIME


# ERC20_config['contract_abi_string'] = dai_abi.abi
# ERC20_config['contract_address'] = config.ETH_CONTRACT_ADDRESS

# ERC20_config['master_wallet_private_key'] = config.MASTER_WALLET_PRIVATE_KEY
# ERC20_config['force_eth_disbursement_amount'] = config.FORCE_ETH_DISBURSEMENT_AMOUNT
# ERC20_config['withdraw_to_address'] = config.WITHDRAW_TO_ADDRESS


# client = Client(config.SENTRY_SERVER_DSN)


celery_app = Celery('tasks',
                    broker=config.REDIS_URL,
                    backend=config.REDIS_URL,
                    task_serializer='json')

red = redis.Redis.from_url(config.REDIS_URL)



contract_registry = ContractRegistry(w3=ERC20_config['w3'])

contract_registry.register_contract(
    config.ETH_CONTRACT_ADDRESS,
    dai_abi.abi,
    'Dai Stablecoin v1.0'
)

blockchain_processor = TransactionProcessor(**ERC20_config, contract_registry=contract_registry)

import eth_trans_manager.celery_tasks

from eth_trans_manager.models import session, BlockchainTransaction, BlockchainTask

b = session.query(BlockchainTask).filter(BlockchainTask.status == 'FAILED').all()