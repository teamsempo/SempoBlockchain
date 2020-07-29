import itertools

class MockRedis(object):

    def delete(self, *args, **kwargs):
        return True

    def lock(self, *args, **kwargs):
        return MockRedisLock()


class MockRedisLock(object):
    def acquire(self, *args, **kwargs):
        return True

    def reacquire(self, *args, **kwargs):
        return True

    def release(self, *args, **kwargs):
        return True

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        pass


class MockContractRegistry(object):
    def get_contract_function(self):
        return lambda x: x


class MockW3(object):
    pass


class MockEth(object):

    def getBalance(self, address):
        return 1000000000000000000000


class MockNonce(object):

    def get_transaction_count(self, address, block_identifier=None):
        return self.addresses.get(address, 0)

    def increment_counter(self, address):

        if address not in self.addresses:
            self.addresses[address] = 1
        else:
            self.addresses[address] += 1

    def __init__(self):
        self.addresses = {}

class MockSendRawTxn(object):

    def send(self, txn):
        self.sent_txns.append(txn)

    def __init__(self):
        self.sent_txns = []

class MockUnbuiltTransaction(object):

    def estimateGas(self, transaction):
        return 100000