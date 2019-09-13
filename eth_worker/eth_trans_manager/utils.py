import requests
from requests.auth import HTTPBasicAuth

from eth_trans_manager import blockchain_processor
from eth_trans_manager.ABIs import dai_abi


def register_contracts_from_app(host_address, auth_username, auth_password):

    token_req = requests.get(host_address + '/api/token', auth=HTTPBasicAuth(auth_username, auth_password))

    for token in token_req.json()['data']['tokens']:
        blockchain_processor.registry.register_contract(token['address'], dai_abi.abi)