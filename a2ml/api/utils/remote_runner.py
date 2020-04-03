from auger.api.credentials import Credentials

import asyncio
import json
import jsonpickle
import requests
import websockets

def log(*args):
    print(*args)

class RemoteRunner(object):
    CRUD_TO_METHOD = {
        'create': 'post',
        'list': 'get',
        'delete': 'delete',
    }

    def __init__(self, ctx, provider, obj_name = None):
        super(RemoteRunner, self).__init__()
        self.ctx = ctx
        self.obj_name = obj_name
        self.ctx.credentials = Credentials(ctx).load()
        self.server_endpoint = ctx.config.get('server_endpoint')
        self.ws_endpoint = 'ws' + self.server_endpoint[4:]

    def _params(self, *args, **kwargs):
        return {
            'context': jsonpickle.encode(self.ctx),
            'project_name': self.ctx.config.get('name'),
            'args': args,
            'kwargs': kwargs,
        }

    def execute(self, operation_name, *args, **kwargs):
        method_name = self.CRUD_TO_METHOD.get(operation_name)

        if method_name:
            res = self.make_requst(method_name, f'/api/v1/{self.obj_name}s', self._params(*args, **kwargs))
            asyncio.get_event_loop().run_until_complete(self.wait_result(res['data']['request_id']))
        else:
            raise ValueError(f'unknown operation {operation_name}')

    def make_requst(self, method_name, path, params):
        method = getattr(requests, method_name)
        return self.handle_respone(method(f"{self.server_endpoint}{path}", json=params))

    def handle_respone(self, response):
        if response.status_code == 200:
            return response.json()
        else:
            log(f"Request error: {response.status_code} {response.text}")
            raise Exception(f"Request error: {response.status_code} {response.text}")

    async def wait_result(self, request_id):
        async with websockets.connect(self.ws_endpoint + "/ws?id=" + request_id) as websocket:
            while True:
                data = await websocket.recv()
                data = json.loads(data)
                log(data)

                if data.get('type', None) == 'result':
                    break

