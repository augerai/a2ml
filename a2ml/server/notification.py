import asyncio_redis
import redis

from a2ml.server.config import Config

config = Config()

class SyncSender:
    def __init__(self):
        self.connection = None

    def publish(self, transaction_id, message):
        if not self.connection:
            self._open()

        self.connection.publish(transaction_id, message)

    def _open(self):
        self.connection = redis.Redis(host=config.redis_host, port=config.redis_port)

    def close(self):
        if self.connection:
            self.connection.close()

    # support with
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class AsyncReceiver:
    def __init__(self, transaction_id):
        self.connection = None
        self.transaction_id = transaction_id

    async def _open(self):
        self.connection = await asyncio_redis.Connection.create(config.redis_host, config.redis_port)
        self.subscriber = await self.connection.start_subscribe()
        await self.subscriber.subscribe([self.transaction_id])

    async def get_message(self):
        if not self.connection:
            await self._open()

        reply = await self.subscriber.next_published()
        return reply.value

    def close(self):
        if self.connection:
            self.connection.close()

    # support with
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
