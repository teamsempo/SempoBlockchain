from eth_manager import red, w3
import json
from web3 import (
    Web3,
    WebsocketProvider,
    HTTPProvider
)
ERC20_ABI =  """
[
    {
        "constant": true,
        "inputs": [],
        "name": "name",
        "outputs": [
            {
                "name": "",
                "type": "string"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [
            {
                "name": "_spender",
                "type": "address"
            },
            {
                "name": "_value",
                "type": "uint256"
            }
        ],
        "name": "approve",
        "outputs": [
            {
                "name": "",
                "type": "bool"
            }
        ],
        "payable": false,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [
            {
                "name": "",
                "type": "uint256"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [
            {
                "name": "_from",
                "type": "address"
            },
            {
                "name": "_to",
                "type": "address"
            },
            {
                "name": "_value",
                "type": "uint256"
            }
        ],
        "name": "transferFrom",
        "outputs": [
            {
                "name": "",
                "type": "bool"
            }
        ],
        "payable": false,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "decimals",
        "outputs": [
            {
                "name": "",
                "type": "uint8"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [
            {
                "name": "_owner",
                "type": "address"
            }
        ],
        "name": "balanceOf",
        "outputs": [
            {
                "name": "balance",
                "type": "uint256"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "symbol",
        "outputs": [
            {
                "name": "",
                "type": "string"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [
            {
                "name": "_to",
                "type": "address"
            },
            {
                "name": "_value",
                "type": "uint256"
            }
        ],
        "name": "transfer",
        "outputs": [
            {
                "name": "",
                "type": "bool"
            }
        ],
        "payable": false,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [
            {
                "name": "_owner",
                "type": "address"
            },
            {
                "name": "_spender",
                "type": "address"
            }
        ],
        "name": "get_allowance",
        "outputs": [
            {
                "name": "",
                "type": "uint256"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "payable": true,
        "stateMutability": "payable",
        "type": "fallback"
    },
    {
        "anonymous": false,
        "inputs": [
            {
                "indexed": true,
                "name": "owner",
                "type": "address"
            },
            {
                "indexed": true,
                "name": "spender",
                "type": "address"
            },
            {
                "indexed": false,
                "name": "value",
                "type": "uint256"
            }
        ],
        "name": "Approval",
        "type": "event"
    },
    {
        "anonymous": false,
        "inputs": [
            {
                "indexed": true,
                "name": "from",
                "type": "address"
            },
            {
                "indexed": true,
                "name": "to",
                "type": "address"
            },
            {
                "indexed": false,
                "name": "value",
                "type": "uint256"
            }
        ],
        "name": "Transfer",
        "type": "event"
    }
]
"""


# Hit the database to get the latest block number to which we're synced
def get_latest_block_number():
    pass

# Call webhook
def call_webhook():
    pass

# Basic 'update' function that gets everything since the database's latest block
def sync_app_to_blockchain():
    # Some logic to chunk up start_block->end_block range. 
    pass

# Do the above, but for every filter as well. This will be called by the celery_tasks task
def sync_all_filters_to_app():
    pass
    #for f in filters:
    #   sync_app_to_blockchain(f)

def synchronize_third_party_transactions():
    # Get list of filters from redis
    filters = json.loads(red.get('third_party_sync_filters'))
    # Since the webook will timeout if we ask for too many blocks at once, we have to break 
    # the range we want into chunks. Here `##__max_enqueued_block` is the highest chunk we
    # either have already gotten, or has been enqued to get
    for f in filters:
        MAX_ENQUEUED_BLOCK = f'{f["id"]}_max_enqueued_block' #todo: rename and tidy this
        max_enqueued_block = red.get(MAX_ENQUEUED_BLOCK) or f['last_block_synchronized']
        latest_block = w3.eth.getBlock('latest').number


        print(f)
        get_blockchain_transaction_history(f['contract_address'], 1,2)
        print(f)
    pass

def handle_event(event):
    print(
        f"""
        Found transaction {event.transactionHash.hex()}
        Block: {event.blockNumber}
        From: {event.args['from']}
        To: {event.args['to']}
        Amount: {event.args['value']}""")

# Gets blockchain transaction history for given range
def get_blockchain_transaction_history(contract_address, start_block, end_block = 'lastest'):
    print('getting history')
    print('abc')
    print('abc')

    erc20_address = Web3.toChecksumAddress(contract_address)
    erc20_contract = w3.eth.contract(
        address=erc20_address,
        abi=ERC20_ABI
    )

    filt = erc20_contract.events.Transfer.createFilter(
        fromBlock=10265073,
        toBlock='latest'
    )

    filters = json.loads(red.get('third_party_sync_filters'))

    for filter in filters:
        print(filter)

    for event in filt.get_all_entries():
        print('pi')
        handle_event(event)
        print('zza')

    pass
    #erc20_contract.events.Transfer.createFilter(
    #    fromBlock=10162000,
    #    toBlock='latest',
    #)