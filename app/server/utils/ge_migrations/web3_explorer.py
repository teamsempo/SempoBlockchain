from flask import current_app
from web3 import Web3
from server.utils.ge_migrations import erc20_abi
from server import ge_w3


def get_token_balance(wallet_address, contract_address):
    cs_contract_address = Web3.toChecksumAddress(contract_address)
    cs_wallet_address = Web3.toChecksumAddress(wallet_address)

    token = ge_w3.eth.contract(address=cs_contract_address, abi=erc20_abi.abi)
    bal = token.functions.balanceOf(cs_wallet_address).call()
    return bal
