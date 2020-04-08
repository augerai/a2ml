from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, ANY

from a2ml.server.server import app
from a2ml.tasks_queue.tasks_api import new_project_task, list_projects_task, delete_project_task, select_project_task, \
    new_dataset_task, list_datasets_task, delete_dataset_task, select_dataset_task, \
    import_data_task

client = TestClient(app)

class TestServer():
    TEST_SCHEMA = {
        '/api/v1/datasets': {
            'get': list_datasets_task,
            'post': new_dataset_task,
            'delete': delete_dataset_task,
            'patch': select_dataset_task,
        },
        '/api/v1/projects': {
            'get': list_projects_task,
            'post': new_project_task,
            'delete': delete_project_task,
            'patch': select_project_task,
        },
        '/api/v1/import_data': {
            'patch': import_data_task,
        },
    }

    def test_hello(self):
        response = client.get('/hello')
        assert response.status_code == 200
        assert response.json() == {'Hello': 'World'}


    @classmethod
    def define_tests(cls):
        for path in cls.TEST_SCHEMA.keys():
            for verb in cls.TEST_SCHEMA[path].keys():
                task = cls.TEST_SCHEMA[path][verb]
                cls.define_test(verb, path, task)

    @classmethod
    def define_test(cls, http_verb, path, task):
        def test(self):
            with patch.object(task, 'delay') as mock_method:
                http_method = getattr(client, http_verb)
                response = http_method(path + '?arg1=11', json={'arg2': 22})
                assert response.status_code == 200

                body = response.json()
                assert body['meta'] == { 'status': 200 }
                assert isinstance(body['data']['request_id'], str)

            mock_method.assert_called_once_with({
                'arg1': '11',
                'arg2': 22,
                '_request_id': ANY
            })


        setattr(cls, f'test_{http_verb}' + path.replace('/', '_'), test)

TestServer.define_tests()
