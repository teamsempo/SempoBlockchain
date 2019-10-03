# https://stackoverflow.com/questions/54617308/pip-install-produces-the-following-error-on-mac-error-command-gcc-failed-wit
# python3.7 / concurrent / futures/thread.py line 135 was originally self._work_queue = queue.SimpleQueue()

from celery import Celery
from raven import Client
import redis
from time import sleep

from requests.exceptions import ConnectionError
from web3 import (
    Web3,
    WebsocketProvider,
    HTTPProvider
)

import os
import sys
parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(parent_dir)
sys.path.append(os.getcwd())

import config
from sql_persistence.interface import SQLPersistenceInterface

from eth_manager.ABIs import dai_abi
from eth_manager.processor import TransactionProcessor, ContractRegistry
from eth_manager.exceptions import WalletExistsError
from eth_manager import utils

eth_config = dict()
eth_config['ethereum_chain_id'] = config.ETH_CHAIN_ID
eth_config['gas_price_gwei'] = config.ETH_GAS_PRICE
eth_config['gas_limit'] = config.ETH_GAS_LIMIT

ETH_CHECK_TRANSACTION_RETRIES = config.ETH_CHECK_TRANSACTION_RETRIES
ETH_CHECK_TRANSACTION_RETRIES_TIME_LIMIT = config.ETH_CHECK_TRANSACTION_RETRIES_TIME_LIMIT
ETH_CHECK_TRANSACTION_BASE_TIME = config.ETH_CHECK_TRANSACTION_BASE_TIME


celery_app = Celery('tasks',
                    broker=config.REDIS_URL,
                    backend=config.REDIS_URL,
                    task_serializer='json')

celery_app.conf.beat_schedule = {
    "maintain_eth_balances": {
        "task": utils.eth_endpoint('topup_wallets'),
        "schedule": 10.0
    },
}

w3 = Web3(HTTPProvider(config.ETH_HTTP_PROVIDER))

red = redis.Redis.from_url(config.REDIS_URL)

persistence_interface = SQLPersistenceInterface(w3=w3)

blockchain_processor = TransactionProcessor(**eth_config,
                                            w3=w3,
                                            persistence_interface=persistence_interface)

import eth_manager.celery_tasks

blockchain_processor.registry.register_contract(
    config.ETH_CONTRACT_ADDRESS,
    dai_abi.abi,
    contract_name='Dai Stablecoin v1.0'
)


from eth_manager.utils import register_contracts_from_app

# Register the master wallet so we can use it for tasks
try:
    persistence_interface.create_blockchain_wallet_from_private_key(config.MASTER_WALLET_PRIVATE_KEY)
except WalletExistsError:
    pass

contracts_registered = False
attempts = 0
while contracts_registered is False and attempts < 100:
    try:
        register_contracts_from_app(config.APP_HOST,
                                    config.INTERNAL_AUTH_USERNAME,
                                    config.INTERNAL_AUTH_PASSWORD)

        contracts_registered = True

    except ConnectionError:
        attempts += 1
        sleep(1)

