from worker.ABIs import standard_erc20_abi, ccv_abi, mintable_abi, dai_abi
from web3 import Web3, HTTPProvider, WebsocketProvider

import config

wallet_private_key   = 'cdd324077dcfc5fc793d7ad7ec34f1751842f8f82f36f4942257fa07ec6a288c'
wallet_address       = '0x9e7651e8E746c9570A983a9175C9Ae64167688f4'

random_add = Web3.toChecksumAddress('0x9e7651e8e746c9570a983a9175c9ae64167688f4')

w3 = Web3(WebsocketProvider("wss://kovan.infura.io/ws/d2d82e65ea724c99b37b0511b225dec4"))

dai_contract = w3.eth.contract(address=Web3.toChecksumAddress('0xc4375b7de8af5a38a93548eb8453a498222c4ff2'), abi=dai_abi.abi)

import time

def handle_event(event):
    print(event)

def log_loop(event_filter, poll_interval):
    while True:
        print('here')
        for event in event_filter.get_new_entries():
            handle_event(event)
        time.sleep(poll_interval)

def main():
    block_filter = w3.eth.filter('latest')
    log_loop(block_filter, 2)
#
# if __name__ == '__main__':
#     main()
#


#
# erc_contract = w3.eth.contract(address=Web3.toChecksumAddress('0x7d184107d54d4401266e1bf61a103719025972cd'), abi=standard_erc20_abi.abi)
#
# ccv_contract = w3.eth.contract(address=Web3.toChecksumAddress('0x7d184107d54d4401266e1bf61a103719025972cd'), abi=ccv_abi.abi)
#
# # ballot_contract = w3.eth.contract(address=Web3.toChecksumAddress('0x171cf5aab40d654b2ea1a74cfe389dd75d6fd287'), abi=ballot_abi.abi)
#
# # g = ballot_contract.functions.vote(1).estimateGas()
#
# # erc_approve = erc_contract.functions.approve(random_add, 1000)
#
# dai_approve = dai_contract.functions.approve(random_add, 1000)
#
# ccv_approve = ccv_contract.functions.approve(random_add, 1000)
#
# # erc_gas = erc_approve.estimateGas()
#
# dai_gas = dai_approve.estimateGas()
#
# ccv_gas = ccv_approve.estimateGas()
#
# nonce = w3.eth.getTransactionCount(wallet_address, block_identifier='pending')
#
# txn_dict = dai_approve.buildTransaction({
#         'chainId': 42,
#         'gas': 140000,
#         'gasPrice': w3.toWei('3', 'gwei'),
#         'nonce': nonce,
#     })
#
# signed_txn = w3.eth.account.signTransaction(txn_dict, private_key=wallet_private_key)
#
# result = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
#
# ttt = 3
#
# tx_receipt = w3.eth.getTransactionReceipt(result)
#
# eee = 4