from auger.api.credentials import Credentials

import asyncio
import json
import jsonpickle
import requests
import sys
import websockets

def show_output(data):
    if isinstance(data, dict):
        data_type = data.get('type', None)

        if  data_type == 'log':
            sys.stdout.write('\b')
            print(data['msg'])
        elif  data_type == 'result':
            sys.stdout.write('\b')
            print(data['status'] + ':', data['result'])
    elif isinstance(data, Exception):
        sys.stdout.write('\b')
        print('Error:', data)
    else:
        sys.stdout.write('\b')
        print(data)

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
            show_output(f"Request error: {response.status_code} {response.text}")
            raise Exception(f"Request error: {response.status_code} {response.text}")

    async def spinning_cursor(self):
        while True:
            for cursor in '|/-\\':
                sys.stdout.write(cursor)
                sys.stdout.flush()
                await asyncio.sleep(0.2)
                sys.stdout.write('\b')

    async def wait_result(self, request_id):
        done = False
        last_msg_id = '0'
        while not done:
            try:
                endpoint = self.ws_endpoint + "/ws?id=" + request_id + '&last_msg_id=' + str(last_msg_id)
                async with websockets.connect(endpoint) as websocket:
                    asyncio.run_coroutine_threadsafe(self.spinning_cursor(), asyncio.get_event_loop())

                    while True:
                        data = await websocket.recv()
                        data = json.loads(data)

                        if '_msg_id' in data:
                            last_msg_id = data['_msg_id']

                        show_output(data)

                        if data.get('type', None) == 'result':
                            done = True
                            break
            except Exception as e:
                show_output(e)
                await asyncio.sleep(2)

