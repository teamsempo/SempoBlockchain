import uuid
import os
from eth_keys import keys

class FakeCeleryAsyncResult():
    def __init__(self, result = None, uuid = str(uuid.uuid4())):
        self.id = uuid
        self.result = result
    def __str__(self):
        return self.id
    def get(self, *args, **kwargs):
        return self.result
    def forget(self):
        pass

def deploy_contract(kwargs, args):
    return FakeCeleryAsyncResult()

def call_contract_function(kwargs, args):
    function_results = { 
        'totalSupply': int(1e19),
        'balanceOf': int(1e19),
        'decimals': 18,
        'allowance': int(1e18),
        'default': 18
    }
    if 'function' in kwargs:
        function_name = kwargs['function']
        if function_name in function_results:
            result = function_results[function_name]
        else:
            print('[WARN] Contract function \'${function_name}\' does not have a default simulator result. Using default value')
            result = function_results['default']
    else:
        print('[WARN] Contract function called without \'function\' argument provided in kwargs.')
        result = function_results['default']
    return FakeCeleryAsyncResult(result=result)

def transact_with_contract_function(kwargs, args):
    return FakeCeleryAsyncResult()

def get_task(kwargs, args):
    return FakeCeleryAsyncResult()

def retry_task(kwargs, args):
    return FakeCeleryAsyncResult()

def retry_failed(kwargs, args):
    return FakeCeleryAsyncResult(result={
            'failed_count': 10,
            'pending_count': 2
        })

def create_new_blockchain_wallet(kwargs, args):
    return FakeCeleryAsyncResult(result = keys.PrivateKey(os.urandom(32)).public_key.to_checksum_address())

def deploy_exchange_network(kwargs, args):
    return FakeCeleryAsyncResult(result = keys.PrivateKey(os.urandom(32)).public_key.to_checksum_address())

def deploy_and_fund_reserve_token(kwargs, args):
    return FakeCeleryAsyncResult(result = keys.PrivateKey(os.urandom(32)).public_key.to_checksum_address())

def deploy_smart_token(kwargs, args):
    return FakeCeleryAsyncResult(result = { 
            'smart_token_address': keys.PrivateKey(os.urandom(32)).public_key.to_checksum_address(),
            'subexchange_address': keys.PrivateKey(os.urandom(32)).public_key.to_checksum_address()
    })

def topup_wallet_if_required(kwargs, args):
    return FakeCeleryAsyncResult()

def send_eth(kwargs, args):
    return FakeCeleryAsyncResult()
