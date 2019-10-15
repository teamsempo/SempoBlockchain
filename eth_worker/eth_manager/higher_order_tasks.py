from celery import chain, signature

import config

from eth_manager import (
    utils,
    persistence_interface,
    w3,
)

def topup_wallets():
    wallets = persistence_interface.get_all_wallets()

    for wallet in wallets:
        if (wallet.wei_topup_threshold or 0) > 0:

            last_topup_task_id = wallet.last_topup_task_id

            if last_topup_task_id:
                task = persistence_interface.get_task_from_id(last_topup_task_id)

                if task.status in ['PENDING', 'UNSTARTED']:
                    return

            signature(utils.eth_endpoint('topup_wallet_if_required'),
                      kwargs={
                          'address': wallet.address,
                          'wei_target_balance': wallet.wei_target_balance or 0,
                          'wei_topup_threshold': wallet.wei_topup_threshold
                      }).delay()


def topup_if_required(address, wei_target_balance, wei_topup_threshold):
    balance = w3.eth.getBalance(address)

    if balance <= wei_topup_threshold and wei_target_balance > balance:
        sig = signature(utils.eth_endpoint('send_eth'),
                        kwargs={
                            'signing_address': config.MASTER_WALLET_ADDRESS,
                            'amount_wei': wei_target_balance - balance,
                            'recipient_address': address,
                            'dependent_on_tasks': []
                        })

        task_id = utils.execute_synchronous_task(sig)

        persistence_interface.set_wallet_last_topup_task_id(address, task_id)

        tt = 5