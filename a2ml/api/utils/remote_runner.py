import asyncio
import json
import jsonpickle
import requests
import sys
import time
import os

from a2ml.api.a2ml_credentials import A2MLCredentials
from a2ml.api.utils.file_uploader import FileUploader, OnelineProgressPercentage


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
        'delete': 'delete',
        'list': 'get',
    }

    NON_CRUD_TO_METHOD = {
        'actual': 'post',
        'deploy': 'patch',
        'evaluate': 'patch',
        'history': 'get',
        'import_data': 'patch',
        'leaderboard': 'get',
        'predict': 'post',
        'review': 'patch',
        'select': 'patch',
        'start': 'patch',
        'stop': 'patch',
        'train': 'patch',
    }

    def __init__(self, ctx, provider, obj_name = None):
        super(RemoteRunner, self).__init__()
        providers = ctx.get_providers(provider)
        if len(providers) == 0:
            raise Exception("Please specify provider")

        provider = providers[0]

        self.ctx = ctx
        self.obj_name = obj_name
        self.ctx.credentials = A2MLCredentials(ctx, provider).load()
        self.server_endpoint = ctx.config.get('server_endpoint', os.environ.get('A2ML_SERVER_ENDPOINT'))
        self.ws_endpoint = 'ws' + self.server_endpoint[4:]

    def _params(self, *args, **kwargs):
        return {
            'context': jsonpickle.encode(self.ctx),
            'project_name': self.ctx.config.get('name'),
            'args': args,
            'kwargs': kwargs,
        }

    def get_http_verb_and_path(self, operation_name):
        crud = False

        if operation_name in self.CRUD_TO_METHOD:
            http_verb = self.CRUD_TO_METHOD[operation_name]
            crud = True
        elif operation_name in self.NON_CRUD_TO_METHOD:
            http_verb = self.NON_CRUD_TO_METHOD[operation_name]
        else:
            raise ValueError(f'unknown operation {operation_name}')

        if self.obj_name:
            if crud:
                path = f'/api/v1/{self.obj_name}s'
            else:
                path = f'/api/v1/{self.obj_name}s/{operation_name}'
        else:
            path = f'/api/v1/{operation_name}'

        return (http_verb, path)

    def execute(self, operation_name, *args, **kwargs):
        http_verb, path = self.get_http_verb_and_path(operation_name)
        new_args = self.upload_local_files(operation_name, *args, **kwargs)

        res = self.make_requst(http_verb, path, self._params(*new_args['args'], **new_args['kwargs']))
        asyncio.get_event_loop().run_until_complete(self.wait_result(res['data']['request_id']))

    def make_requst(self, http_verb, path, params={}):
        method = getattr(requests, http_verb)
        return self.handle_respone(method(f"{self.server_endpoint}{path}", json=params))

    def handle_respone(self, response):
        if response.status_code == 200:
            return response.json()
        else:
            show_output(f"Request error: {response.status_code} {response.text}")
            raise Exception(f"Request error: {response.status_code} {response.text}")

    def handle_weboscket_respone(self, data):
        data_type = data.get('type', None)

        if data_type == 'result' and isinstance(data['result'], dict):
            config = jsonpickle.decode(data['result']['config'])

            original_source = config.get('original_source')
            if original_source:
                config.set('config', 'source', original_source)
                config.remove('config', 'original_source')

            config.write_all()

            data['result'] = data['result']['response']

        show_output(data)

    def get_upload_credentials(self):
        res = self.make_requst('post', '/api/v1/upload_credentials')
        return res['data']

    def local_path(self, path):
        path = path.lower()
        return not(path.startswith('s3://') or path.startswith('http://') or path.startswith('https://'))

    def upload_local_files(self, operation_name, *args, **kwargs):
        file_to_upload = None
        inject_uploaded_file_to_request_func = None

        if operation_name == 'import_data':
            file_to_upload = self.ctx.config.get('source')
            self.ctx.config.set('config', 'original_source', file_to_upload)

            def replacer_func(remote_path):
                self.ctx.config.set('config', 'source', remote_path)
                return {'args': tuple(args), 'kwargs': kwargs}

            inject_uploaded_file_to_request_func = replacer_func
        elif operation_name == 'predict' or (self.obj_name == 'dataset' and operation_name == 'create'):
            file_to_upload = args[0]

            if operation_name != 'predict':
                self.ctx.config.set('config', 'original_source', file_to_upload)

            def replacer_func(remote_path):
                new_args = list(args)
                new_args[0] = remote_path
                return {'args': tuple(new_args), 'kwargs': kwargs}

            inject_uploaded_file_to_request_func = replacer_func

        if file_to_upload and self.local_path(file_to_upload):
            creds = self.get_upload_credentials()

            uploader = FileUploader(
                bucket=creds['bucket'],
                endpoint_url=creds['endpoint_url'],
                access_key=creds['access_key'],
                secret_key=creds['secret_key'],
                session_token=creds['session_token'],
            )

            url = uploader.multi_part_upload(file_to_upload, callback=OnelineProgressPercentage(file_to_upload))

            return inject_uploaded_file_to_request_func(url)
        else:
            return {'args': args, 'kwargs': kwargs}

    async def spinning_cursor(self):
        while True:
            for cursor in '|/-\\':
                sys.stdout.write(cursor)
                sys.stdout.flush()
                await asyncio.sleep(0.2)
                sys.stdout.write('\b')

    async def wait_result(self, request_id):
        import websockets

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

                        self.handle_weboscket_respone(data)

                        if data.get('type', None) == 'result':
                            done = True
                            break
            except Exception as e:
                show_output(e)
                await asyncio.sleep(2)

