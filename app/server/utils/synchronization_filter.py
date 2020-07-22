from server import bt

def add_transaction_filter(contract_address, contract_type, filter_parameters, filter_type, decimals = None, block_epoch = None):
    transaction_filter = {
        'contract_address': contract_address,
        'contract_type': contract_type,
        'filter_parameters': filter_parameters,
        'filter_type': filter_type,
        'decimals': decimals,
        'block_epoch': block_epoch
    }
    bt.add_transaction_sync_filter(transaction_filter)
    return transaction_filter
