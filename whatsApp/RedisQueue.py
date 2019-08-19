import redis, uuid, datetime
from json import dumps, loads


class RedisQueue(object):
    """Simple Queue with Redis Backend"""

    def __init__(self, queue_name, **kwargs):
        """The default connection parameters are: host='localhost', port=6379, db=0"""
        self.__db = redis.from_url(**kwargs)
        self.queue_name = queue_name

    def qsize(self):
        """Return the approximate size of the queue."""
        return self.__db.llen(self.queue_name)

    def empty(self):
        """Return True if the queue is empty, False otherwise."""
        return self.qsize() == 0

    def put(self, data):
        """Put item into the queue."""

        qt = QueueTask(self, {'data': data})

        self.__db.rpush(self.queue_name, dumps(qt.serialize()))

        return qt

    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue.

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available."""
        if block:
            item = self.__db.blpop(self.queue_name, timeout=timeout)
        else:
            item = self.__db.lpop(self.queue_name)

        if item is not None:
            return QueueTask(self, loads(item))
        else:
            return None

    def get_nowait(self):
        """Equivalent to get(False)."""
        return self.get(False)

    def set_info(self, id, data, ex=60 * 60 * 10):
        self.__db.set(self.queue_name + ':' + str(id), dumps({'id': id, 'data': data}), ex=ex)

    def get_info(self, id):
        item = self.__db.get(self.queue_name + ':' + str(id))

        if item is not None:
            return loads(item)
        else:
            return None


class QueueTask(object):

    def __init__(self, parent_queue, task_info):

        self._parent_queue = parent_queue
        self._response = None

        self.data = task_info.get('data')

        id = task_info.get('id')

        if id == None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id

    def __str__(self):
        return "<Task, id: {}>".format(self.id)

    def serialize(self):
        return {'id': self.id, 'data': self.data}

    def set_response(self, data):
        self._response = data
        self._parent_queue.set_info(self.id, data, ex=60 * 60 * 10)

    def get_response(self):
        if self._response is None:
            response = self._parent_queue.get_info(self.id)

            if response is not None:
                self._response = response

        return self._response
