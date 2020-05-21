import asyncio
import json
import jsonpickle
import requests
import sys
import time
import os
import websockets

from a2ml.api.utils import fsclient, dict_dig
from a2ml.api.a2ml_credentials import A2MLCredentials
from a2ml.api.utils.file_uploader import FileUploader, OnelineProgressPercentage


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
        self.server_endpoint = ctx.config.get('server_endpoint', os.environ.get('A2ML_SERVER_ENDPOINT'))
        self.ws_endpoint = 'ws' + self.server_endpoint[4:]
        self.provider = provider

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
        try:
            creds = A2MLCredentials(self.ctx, self.provider)
            creds.load()
            creds.verify()
            self.ctx.credentials = creds.serialize()

            http_verb, path = self.get_http_verb_and_path(operation_name)
            new_args, uploaded_file, local_file = self.upload_local_files(operation_name, *args, **kwargs)

            params = self._params(*new_args['args'], **new_args['kwargs'])

            if uploaded_file:
                params['tmp_file_to_remove'] = uploaded_file

            res = self.make_requst(http_verb, path, params)
            return self.get_event_loop().run_until_complete(self.wait_result(res['data']['request_id'], local_file))
        except Exception as exc:
            if self.ctx.debug:
                import traceback
                traceback.print_exc()

            self.ctx.log(str(exc))

            return {
                self.provider: {
                    'result': False,
                    'data': str(exc)
                }
            }

    def get_event_loop(self):
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            return asyncio.new_event_loop()

    def make_requst(self, http_verb, path, params={}):
        method = getattr(requests, http_verb)
        return self.handle_respone(method(f"{self.server_endpoint}{path}", json=params))

    def handle_respone(self, response):
        if response.status_code == 200:
            return response.json()
        else:
            self.show_output(f"Request error: {response.status_code} {response.text}")
            raise Exception(f"Request error: {response.status_code} {response.text}")

    def handle_weboscket_respone(self, data, local_file):
        data_type = self.get_response_data_type(data)

        if data_type == 'result' and isinstance(data['result'], dict):
            config = jsonpickle.decode(data['result']['config'])

            original_source = config.get('original_source')
            if original_source:
                config.set('source', original_source, config_name="config")
                config.remove('config', 'original_source')

            config.write_all()

            data['result'] = data['result']['response']
            self.download_prediction_result(data['result'], local_file)

        self.show_output(data)

    def download_prediction_result(self, results, local_file):
        for provider in results.keys():
            result = results[provider]
            predicted = dict_dig(result, 'data', 'predicted')
            if predicted and type(predicted)==str and fsclient.is_s3_path(predicted):
                file_path = os.path.splitext(local_file)[0] + '_predicted.csv'
                client = self.create_uploader()
                client.download(predicted, file_path)
                result['data']['predicted'] = file_path

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
            self.ctx.config.set('original_source', file_to_upload, config_name="config")

            def replacer_func(remote_path):
                self.ctx.config.set('source', remote_path, config_name="config")
                return {'args': tuple(args), 'kwargs': kwargs}

            inject_uploaded_file_to_request_func = replacer_func
        elif operation_name == 'predict' or (self.obj_name == 'dataset' and operation_name == 'create'):
            file_to_upload = args[0]

            if operation_name != 'predict':
                self.ctx.config.set('original_source', file_to_upload, config_name="config")

            def replacer_func(remote_path):
                new_args = list(args)
                new_args[0] = remote_path
                return {'args': tuple(new_args), 'kwargs': kwargs}

            inject_uploaded_file_to_request_func = replacer_func

        if file_to_upload and self.local_path(file_to_upload):
            uploader = self.create_uploader()
            url = uploader.multi_part_upload(file_to_upload, callback=OnelineProgressPercentage(file_to_upload))

            return inject_uploaded_file_to_request_func(url), url, file_to_upload
        else:
            return {'args': args, 'kwargs': kwargs}, None, None

    def create_uploader(self):
        creds = self.get_upload_credentials()

        return FileUploader(
            bucket=creds['bucket'],
            endpoint_url=creds['endpoint_url'],
            access_key=creds['access_key'],
            secret_key=creds['secret_key'],
            session_token=creds['session_token'],
        )

    def get_response_data_type(self, data):
        if isinstance(data, dict):
            return data.get('type', None)

    def show_output(self, data):
        if isinstance(data, dict):
            data_type = data.get('type', None)

            if  data_type == 'log':
                sys.stdout.write('\b')
                print(data['msg'])
            elif  data_type == 'result':
                if self.ctx.debug:
                    sys.stdout.write('\b')
                    print(data['status'] + ':', data['result'])
        elif isinstance(data, Exception):
            if self.ctx.debug:
                import traceback;
                traceback.print_exc()

            sys.stdout.write('\b')
            print('Error:', data)
        else:
            sys.stdout.write('\b')
            print(data)

    async def spinning_cursor(self):
        while True:
            for cursor in '|/-\\':
                sys.stdout.write(cursor)
                sys.stdout.flush()
                await asyncio.sleep(0.2)
                sys.stdout.write('\b')

    async def wait_result(self, request_id, local_file):
        done = False
        data = {}
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

                        self.handle_weboscket_respone(data, local_file)

                        if self.get_response_data_type(data) == 'result':
                            done = True
                            break
            except Exception as e:
                self.show_output(e)
                await asyncio.sleep(2)
            finally:
                if self.get_response_data_type(data) == 'result':
                    done = True
                    break

        if data.get('result'):
            return data.get('result')

        return {
            self.provider: {
                'result': False,
                'data': "Server error. Please try again..."
            }
        }
