# https://stackoverflow.com/questions/54617308/pip-install-produces-the-following-error-on-mac-error-command-gcc-failed-wit
# python3.7 / concurrent / futures/thread.py line 135 was originally self._work_queue = queue.SimpleQueue()

from celery import Celery, beat, Task
from raven import Client
import redis

from web3 import (
    Web3,
    WebsocketProvider,
)

import config
from eth_worker.ABIs import dai_abi

ERC20_config = {}
ERC20_config['ethereum_chain_id'] = config.ETH_CHAIN_ID
# ERC20_config['http_provider'] = config.ETH_HTTP_PROVIDER
ERC20_config['gas_price_gwei'] = config.ETH_GAS_PRICE
ERC20_config['gas_limit'] = config.ETH_GAS_LIMIT
ERC20_config['w3'] = Web3(WebsocketProvider(config.ETH_WEBSOCKET_PROVIDER))

ETH_CHECK_TRANSACTION_RETRIES = config.ETH_CHECK_TRANSACTION_RETRIES
ETH_CHECK_TRANSACTION_RETRIES_TIME_LIMIT = config.ETH_CHECK_TRANSACTION_RETRIES_TIME_LIMIT
ETH_CHECK_TRANSACTION_BASE_TIME = config.ETH_CHECK_TRANSACTION_BASE_TIME


ERC20_config['contract_abi_string'] = dai_abi.abi
ERC20_config['contract_address'] = config.ETH_CONTRACT_ADDRESS

# ERC20_config['master_wallet_private_key'] = config.MASTER_WALLET_PRIVATE_KEY
# ERC20_config['force_eth_disbursement_amount'] = config.FORCE_ETH_DISBURSEMENT_AMOUNT
# ERC20_config['withdraw_to_address'] = config.WITHDRAW_TO_ADDRESS


# client = Client(config.SENTRY_SERVER_DSN)


celery_app = Celery('tasks',
                    broker=config.REDIS_URL,
                    backend=config.REDIS_URL,
                    task_serializer='json')

red = redis.Redis.from_url(config.REDIS_URL)


import eth_worker.celery_tasks

from eth_worker.processor import ContractRegistry
