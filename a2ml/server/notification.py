import aioredis
import asyncio
import json
import redis

from a2ml.server.config import Config

config = Config()

class SyncSender:
    def __init__(self):
        self.connection = None

    def publish(self, request_id, message):
        if config.notificator_redis_host:
            if not self.connection:
                self._open()

            if isinstance(message, dict):
                message = json.dumps(message)

            self.connection.xadd(request_id, {'json': message})
        else:
            # Not set NOTIFICATOR_REDIS_HOST env var if worker is run as Hub worker witouh A2ML server
            # in this case worker will not try to notify about progress
            pass

    def publish_result(self, request_id, status, result):
        self.publish(
            request_id,
            {'type': 'result', 'status': status, 'result': result}
        )

    def publish_log(self, request_id, level, msg, *args, **kwargs):
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
    def __init__(self, request_id, last_msg_id):
        self.connection = None
        self.request_id = request_id
        self.last_msg_id = last_msg_id

    async def _open(self):
        self.connection = await aioredis.create_redis(
            'redis://' + config.notificator_redis_host + ':' + str(config.notificator_redis_port)
        )

    async def get_message(self, timeout=5):
        if not self.connection:
            await self._open()

        res = await self.connection.xread([self.request_id], timeout=timeout, count=1, latest_ids=[self.last_msg_id])
        if len(res) > 0:
            msg = res[0]
            self.last_msg_id = msg[1]
            data = json.loads(msg[2][b'json'])
            data['_msg_id'] = self.last_msg_id.decode('utf-8')
            return json.dumps(data)
        else:
            return None

    async def close(self):
        if self.connection:
            self.connection.close()
            await self.connection.wait_closed()
