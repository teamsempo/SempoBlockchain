
class MockRedis(object):

    def delete(self, *args, **kwargs):
        return True

    def lock(self, *args, **kwargs):
        return MockLock()


class MockLock(object):
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        pass