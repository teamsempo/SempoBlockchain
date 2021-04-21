from eth_manager.eth_transaction_processor import EthTransactionProcessor


class CeloTransactionProcessor(EthTransactionProcessor):

    def _construct_full_txn_dict(self, metadata, partial_txn_dict=None, unbuilt_transaction=None):

        if not partial_txn_dict and not unbuilt_transaction:
            raise Exception("Must provide partial_txn_dict and/or unbuilt_transaction data")

        if not partial_txn_dict:
            partial_txn_dict = {}

        txn_dict = {**metadata, **partial_txn_dict, **self.celo_txn_data}

        if unbuilt_transaction:
            txn_dict = unbuilt_transaction.buildTransaction(txn_dict)

        return txn_dict

    celo_txn_data = {
        'feeCurrency': None,
        'gatewayFeeRecipient': None,
        'gatewayFee': 0
    }