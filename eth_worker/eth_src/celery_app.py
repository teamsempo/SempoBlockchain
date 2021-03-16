# https://stackoverflow.com/questions/54617308/pip-install-produces-the-following-error-on-mac-error-command-gcc-failed-wit
# python3.7 / concurrent / futures/thread.py line 135 was originally self._work_queue = queue.SimpleQueue()
from celery import Celery
import sentry_sdk
from sentry_sdk import configure_scope
from sentry_sdk.integrations.celery import CeleryIntegration
import redis, requests

from requests.auth import HTTPBasicAuth
from web3 import (
    Web3,
    HTTPProvider,
    WebsocketProvider
)

from web3.exceptions import BadFunctionCallOutput

import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)
grandparent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(grandparent_dir)

import config
from sql_persistence import session
from sql_persistence.interface import SQLPersistenceInterface

from eth_manager.contract_registry.ABIs import (
    erc20_abi,
    bancor_converter_abi,
    bancor_network_abi
)

from eth_manager.eth_transaction_processor import EthTransactionProcessor
from eth_manager.transaction_supervisor import TransactionSupervisor
from eth_manager.task_manager import TaskManager
from eth_manager.blockchain_sync.blockchain_sync import BlockchainSyncer

import celery_utils

sentry_sdk.init(config.SENTRY_SERVER_DSN, integrations=[CeleryIntegration()])
with configure_scope() as scope:
    scope.set_tag("domain", config.APP_HOST)

chain_config = config.CHAINS[celery_utils.chain]

from config import logg

logg.info(f'Using chain {celery_utils.chain}')

app = Celery('tasks',
             broker=config.REDIS_URL,
             backend=config.REDIS_URL,
             task_serializer='json'
             )

app.conf.redbeat_lock_key = f'redbeat:lock:{config.REDBEAT_LOCK_ID}'

app.conf.beat_schedule = {
    "maintain_eth_balances": {
        "task": celery_utils.eth_endpoint('topup_wallets'),
        "schedule": 600.0
    },
}
app.conf.beat_schedule = {
    'third-party-transaction-sync': {
        'task': celery_utils.eth_endpoint('synchronize_third_party_transactions'),
        'schedule': chain_config['THIRD_PARTY_SYNC_SCHEDULE'],
    }
}

w3 = Web3(HTTPProvider(chain_config['HTTP_PROVIDER']))

w3_websocket = Web3(WebsocketProvider(chain_config['WEBSOCKET_PROVIDER']))

if celery_utils.chain == 'CELO':
    from web3.middleware import geth_poa_middleware
    from celo_eth_account.account import Account
    from celo_integration import CeloTransactionProcessor

    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    w3_websocket.middleware_onion.inject(geth_poa_middleware, layer=0)
    w3.eth.account = Account

    TransactionProcessorClass = CeloTransactionProcessor
else:
    TransactionProcessorClass = EthTransactionProcessor

red = redis.Redis.from_url(config.REDIS_URL)

first_block_hash = w3.eth.getBlock(0).hash.hex()

persistence_module = SQLPersistenceInterface(
    red=red, session=session, first_block_hash=first_block_hash
)

processor = TransactionProcessorClass(
    ethereum_chain_id=chain_config['CHAIN_ID'],
    gas_price_wei=w3.toWei(chain_config['GAS_PRICE'], 'gwei'),
    gas_limit=chain_config['GAS_LIMIT'],
    w3=w3,
    persistence=persistence_module
)

supervisor = TransactionSupervisor(
    red=red,
    persistence=persistence_module,
    processor=processor
)

task_manager = TaskManager(persistence=persistence_module, transaction_supervisor=supervisor)

blockchain_sync = BlockchainSyncer(persistence=persistence_module, red=red, w3_websocket=w3_websocket)

if os.environ.get('CONTAINER_TYPE') == 'PRIMARY':
    persistence_module.create_blockchain_wallet_from_private_key(
        chain_config['MASTER_WALLET_PRIVATE_KEY'],
        allow_existing=True
    )

processor.registry.register_abi('ERC20', erc20_abi.abi)
processor.registry.register_abi('bancor_converter', bancor_converter_abi.abi)
processor.registry.register_abi('bancor_network', bancor_network_abi.abi)

import celery_tasks

import redbeat
