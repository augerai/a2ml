import asyncio_redis
import json
import redis

from a2ml.server.config import Config

config = Config()

class SyncSender:
    def __init__(self):
        self.connection = None

    def publish(self, request_id, message):
        if not self.connection:
            self._open()

        if isinstance(message, dict):
            message = json.dumps(message)

        self.connection.publish(request_id, message)

    def publish_result(self, request_id, status, result):
        self.publish(
            request_id,
            {'type': 'result', 'status': status, 'result': result}
        )

    def publish_log(self, request_id, level, msg, args, kwargs):
        self.publish(
            request_id,
            {'type': 'log', 'level': level, 'msg': msg, 'args': args, 'kwargs': kwargs}
        )

    def _open(self):
        self.connection = redis.Redis(
            host=config.notificator_redis_host,
            port=config.notificator_redis_port
        )

    def close(self):
        if self.connection:
            self.connection.close()

    # support with
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class AsyncReceiver:
    def __init__(self, request_id):
        self.connection = None
        self.request_id = request_id

    async def _open(self):
        self.connection = await asyncio_redis.Connection.create(
            config.notificator_redis_host,
            config.notificator_redis_port
        )
        self.subscriber = await self.connection.start_subscribe()
        await self.subscriber.subscribe([self.request_id])

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
