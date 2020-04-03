from auger.api.credentials import Credentials

import asyncio
import json
import jsonpickle
import requests
import websockets

def log(*args):
    print(*args)

class RemoteRunner(object):
    def __init__(self, ctx, provider, obj_name = None):
        super(RemoteRunner, self).__init__()
        self.ctx = ctx
        self.obj_name = obj_name
        self.ctx.credentials = Credentials(ctx).load()
        self.server_endpoint = ctx.config.get('server_endpoint')

    def _params(self):
        return {
            'context': jsonpickle.encode(self.ctx),
            'project_name': self.ctx.config.get('name'),
        }

    def execute(self, operation_name, *args, **kwargs):
        if operation_name == 'create':
            res = self.post_requst(f'/api/v1/{self.obj_name}s', self._params())
        elif operation_name == 'list':
            res = self.get_requst(f'/api/v1/{self.obj_name}s', self._params())
        else:
            raise ValueError(f'unknown operation {operation_name}')

        asyncio.get_event_loop().run_until_complete(self.wait_result(res['data']['request_id']))

    def get_requst(self, path, params):
        return self.handle_respone(requests.get(f"{self.server_endpoint}{path}", json=params))

    def post_requst(self, path, params):
        return self.handle_respone(requests.post(f"{self.server_endpoint}{path}", json=params))


    def handle_respone(self, response):
        if response.status_code == 200:
            return response.json()
        else:
            log(f"Request error: {response.status_code} {response.text}")
            raise Exception(f"Request error: {response.status_code} {response.text}")

    async def wait_result(self, request_id):
        async with websockets.connect("ws://localhost:8000/ws?id=" + request_id) as websocket:
            while True:
                data = await websocket.recv()
                data = json.loads(data)
                log(data)

                if data.get('type', None) == 'result':
                    break

