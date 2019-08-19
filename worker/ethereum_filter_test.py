from web3 import Web3, WebsocketProvider
from worker.ABIs import dai_abi


web3 = Web3(WebsocketProvider('wss://mainnet.infura.io/ws/v3/2261599041f543deb0629fc925e0a121'))
dai_contract = web3.eth.contract(address=Web3.toChecksumAddress('0x89d24a6b4ccb1b6faa2625fe562bdd9a23260359'), abi=dai_abi.abi)


import time

def handle_event(event):
    print(event)

def log_loop(event_filter, poll_interval):
    while True:
        print('heries')
        print('dai contract add:' + dai_contract.address)
        print('filter:')
        print(str(event_filter))

        for event in event_filter.get_new_entries():
            handle_event(event)
        time.sleep(poll_interval)

def filter_loop():
    while True:

        latest_block = web3.eth.getBlock('latest')

        threshold = latest_block.number - 1000

        dai_filter = dai_contract.events.Transfer.createFilter(
            fromBlock=threshold,
            argument_filters={'dst': ['0x68D3ce90D84B4DD8936908Afd4079797057996bB']})

        print('filter is')
        print(str(filter))

        for event in dai_filter.get_all_entries():
            handle_event(event)

        time.sleep(2)

def main():
    dai_filter = dai_contract.events.Transfer.createFilter(
        fromBlock="latest",
        argument_filters={'dst':['0x02d4AE6152792E55ab930b6c635F51812AfA2A2a']})

    block_filter = web3.eth.filter('latest')
    # log_loop(dai_filter, 2)
    filter_loop()

if __name__ == '__main__':
    main()