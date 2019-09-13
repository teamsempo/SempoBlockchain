from server import celery_app

def get_wallet_balance(address, token):
    blockchain_task = celery_app.signature('eth_trans_manager.celery_tasks.call_contract_function',
                                           kwargs={
                                               'contract': token.address,
                                               'function': 'balanceOf',
                                               'args': [address],
                                           })
    result = blockchain_task.delay()

    try:
        balance = result.get(timeout=3, propagate=True, interval=0.3)
    except Exception as e:
        raise e
    finally:
        result.forget()

    return balance / 1e18

