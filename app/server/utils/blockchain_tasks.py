from server import celery_app

def _execute_synchronous_task(signature):
    async_result = signature.delay()

    try:
        response = async_result.get(timeout=1, propagate=True, interval=0.3)
    except Exception as e:
        raise e
    finally:
        async_result.forget()

    return response

def create_blockchain_wallet():

    sig = celery_app.signature('eth_trans_manager.celery_tasks.create_blockchain_wallet')

    return _execute_synchronous_task(sig)


def send_eth(signing_address, recipient_address, amount, dependent_on_tasks=None):

    transfer_sig = celery_app.signature('eth_trans_manager.celery_tasks.send_eth',
                                        kwargs={
                                            'signing_address': signing_address,
                                            'amount': amount,
                                            'recipient_address': recipient_address,
                                            'dependent_on_tasks': dependent_on_tasks
                                        })

    return _execute_synchronous_task(transfer_sig)

def make_token_transfer(signing_address, token,
                        from_address, to_address, amount,
                        dependent_on_tasks=None):

    transfer_sig = celery_app.signature('eth_trans_manager.celery_tasks.transact_with_contract_function',
                                kwargs={
                                    'signing_address': signing_address,
                                    'contract': token.address,
                                    'function': 'transferFrom',
                                    'args': [
                                        from_address,
                                        to_address,
                                        token.system_amount_to_token(amount)
                                    ],
                                    'dependent_on_tasks': dependent_on_tasks
                                })

    return _execute_synchronous_task(transfer_sig)


def make_approval(signing_address, token,
                  spender, amount,
                  dependent_on_tasks=None):

    transfer_sig = celery_app.signature('eth_trans_manager.celery_tasks.transact_with_contract_function',
                                kwargs={
                                    'signing_address': signing_address,
                                    'contract': token.address,
                                    'function': 'approve',
                                    'args': [
                                        spender,
                                        token.system_amount_to_token(amount)
                                    ],
                                    'gas_limit': 46049,
                                    'dependent_on_tasks': dependent_on_tasks
                                })

    return _execute_synchronous_task(transfer_sig)


def get_token_decimals(token):

    decimals_sig = celery_app.signature('eth_trans_manager.celery_tasks.call_contract_function',
                                         kwargs={
                                                      'contract': token.address,
                                                      'function': 'decimals'
                                         })

    return _execute_synchronous_task(decimals_sig)

def get_wallet_balance(address, token):

    balance_sig = celery_app.signature('eth_trans_manager.celery_tasks.call_contract_function',
                                        kwargs={
                                                     'contract': token.address,
                                                     'function': 'balanceOf',
                                                     'args': [address]
                                        })

    balance = _execute_synchronous_task(balance_sig)

    return token.token_amount_to_system(balance)