# https://stackoverflow.com/questions/54617308/pip-install-produces-the-following-error-on-mac-error-command-gcc-failed-wit
# python3.7 / concurrent / futures/thread.py line 135 was originally self._work_queue = queue.SimpleQueue()
from celery import Celery
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
import redis, requests
from time import sleep

from requests.exceptions import ConnectionError
from requests.auth import HTTPBasicAuth
from web3 import (
    Web3,
    WebsocketProvider,
    HTTPProvider
)

from web3.exceptions import BadFunctionCallOutput

import os
import sys
parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(parent_dir)
sys.path.append(os.getcwd())

import config
from sql_persistence.interface import SQLPersistenceInterface

from eth_manager.ABIs import (
    dai_abi,
    erc20_abi,
    bancor_converter_abi,
    bancor_network_abi
)

from eth_manager.processor import TransactionProcessor
from eth_manager.contract_registry import ContractRegistry
from eth_manager.exceptions import WalletExistsError
from eth_manager import utils

sentry_sdk.init(config.SENTRY_SERVER_DSN, integrations=[CeleryIntegration()])

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
        "schedule": 600.0
    },
}

w3 = Web3(HTTPProvider(config.ETH_HTTP_PROVIDER))

red = redis.Redis.from_url(config.REDIS_URL)

persistence_interface = SQLPersistenceInterface(w3=w3, red=red)

blockchain_processor = TransactionProcessor(
    **eth_config,
    w3=w3,
    persistence_interface=persistence_interface
)

import eth_manager.celery_tasks
#
# blockchain_processor.registry.register_contract(
#     config.ETH_CONTRACT_ADDRESS,
#     dai_abi.abi,
#     contract_name='Dai Stablecoin v1.0'
# )

# Register the master wallet so we can use it for tasks

if os.environ.get('CONTAINER_TYPE') == 'PRIMARY':
    persistence_interface.create_blockchain_wallet_from_private_key(
        config.MASTER_WALLET_PRIVATE_KEY,
        allow_existing=True
    )


def register_tokens_from_app(host_address, auth_username, auth_password):
    token_req = requests.get(host_address + '/api/token', auth=HTTPBasicAuth(auth_username, auth_password))

    if token_req.status_code == 200:

        for token in token_req.json()['data']['tokens']:
            try:
                blockchain_processor.registry.register_contract(token['address'], dai_abi.abi)
            except BadFunctionCallOutput as e:
                # It's probably a contract on a different chain
                if not config.IS_PRODUCTION:
                    pass
                else:
                    raise e

        return True

    else:
        return False


blockchain_processor.registry.register_abi('ERC20', erc20_abi.abi)
blockchain_processor.registry.register_abi('bancor_converter', bancor_converter_abi.abi)
blockchain_processor.registry.register_abi('bancor_network', bancor_network_abi.abi)

# contracts_registered = False
# attempts = 0
# while contracts_registered is False and attempts < 10:
#     print('Contract Register Attempt ' + str(attempts))
#     try:
#         contracts_registered = register_tokens_from_app(config.APP_HOST,
#                                                         config.INTERNAL_AUTH_USERNAME,
#                                                         config.INTERNAL_AUTH_PASSWORD)
#
#         if contracts_registered:
#             print('Contracts Registered Successfully')
#
#     except ConnectionError:
#         pass
#
#     attempts += 1
#     sleep(1)
#
