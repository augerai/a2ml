import os
import pytest
from a2ml.tasks_queue.tasks_api import (
    import_data_task,
    evaluate_task,
    train_task,
    deploy_task,
    predict_task,
    new_project_task
)
from a2ml.api.utils.context import Context
from unittest.mock import ANY

pytestmark = pytest.mark.usefixtures('config_context')


class TestTasks(object):

    @pytest.mark.skip(reason='run it locally')
    def test_import(self):
        params = {
            'provider': 'auger',
            'debug_log': True,
            'project_name': 'cli-integration-test'
        }
        import_data_task.s(params).apply()

    @pytest.mark.skip(reason='run it locally')
    def test_import_server(self):
        from a2ml.api.a2ml import A2ML

        ctx = Context(
            path=os.path.join(
                os.environ.get('A2ML_PROJECT_PATH', ''),
                'cli-integration-test'
            ),
            debug=True
        )

        provider = "auger"
        ctx.config.set('config', 'providers', [provider])
        ctx.config.set('config', 'use_server', True)

        A2ML(ctx, provider).import_data()

    @pytest.mark.skip(reason='run it locally')
    def test_list_projects_server(self):
        from a2ml.api.a2ml_project import A2MLProject

        ctx = Context(
            path=os.path.join(
                os.environ.get('A2ML_PROJECT_PATH', ''),
                'cli-integration-test'
            ),
            debug=True
        )
        provider = "azure"
        ctx.config.set('config', 'providers', [provider])
        ctx.config.set('config', 'use_server', True)

        A2MLProject(ctx, provider).list()

    @pytest.mark.skip(reason='run it locally')
    def test_import_s3(self):
        params = {
            'provider': 'auger',
            'debug_log': True,
            'project_name': 'a2ml-app',
            '_request_id': 'some-id',
            'source_path': 's3://sample-bucket/workspace/projects/a2ml-app/files/iris.csv'
        }

        res = import_data_task.s(params).apply()
        assert res == []

    @pytest.mark.skip(reason='run it locally')
    def test_train_server(self):
        from a2ml.api.a2ml import A2ML

        ctx = Context(
            path=os.path.join(
                os.environ.get('A2ML_PROJECT_PATH', ''),
                'cli-integration-test'
            ),
            debug=True
        )

        provider = "azure"
        ctx.config.set('config', 'providers', [provider])
        ctx.config.set('config', 'use_server', True)

        A2ML(ctx, provider).train()

    @pytest.mark.skip(reason='run it locally')
    def test_train_s3(self):
        params = {
            'provider': 'auger',
            'debug_log': True,
            'project_name': 'new-project-test-s3-5',
            # 'source_path': 's3://auger-demo-datasets/a2ml_app/adult.data.csv'
        }

        train_task.s(params).apply()

    @pytest.mark.skip(reason='run it locally')
    def test_evaluate_s3(self):
        params = {
            'provider': 'auger',
            'debug_log': True,
            'project_name': 'new-project-test-s3-5',
            # 'source_path': 's3://auger-demo-datasets/a2ml_app/adult.data.csv'
        }

        res = evaluate_task.s(params).apply()
        print(res)

    @pytest.mark.skip(reason='run it locally')
    def test_deploy_s3(self):
        params = {
            'provider': 'auger',
            'debug_log': True,
            'project_name': 'new-project-test-s3-5',
            'args': ['9E248B642D0E497']
        }

        res = deploy_task.s(params).apply()
        print(res)

    @pytest.mark.skip(reason='run it locally')
    def test_predict_s3(self):
        params = {
            'provider': 'auger',
            'debug_log': True,
            'project_name': 'new-project-test-s3-5',
            'args': [
                's3://auger-demo-datasets/a2ml_app/adult.data_test.csv',
                '9E248B642D0E497',
            ]
        }

        res = predict_task.s(params).apply()
        print(res)

    @pytest.mark.skip(reason='run it locally')
    def test_new_project(self):
        params = {
            'providers': ['auger', 'azure'],
            'debug_log': True,
            'project_name': 'new-project-test',
            'target': 'species',
            'model_type': 'classification'
        }

        params['source_path'] = os.path.join(
            os.environ.get('A2ML_PROJECT_PATH'), "iris.csv")

        new_project_task.s(params).apply()

    @pytest.mark.skip(reason='run it locally')
    def test_new_project_s3(self):
        params = {
            'providers': ['auger', 'azure'],
            'debug_log': True,
            'project_name': 'new-project-test-s3-7',
            'source_path': 's3://auger-demo-datasets/iris_data_sample.csv',
            'target': 'class',
            'model_type': 'classification'
        }

        new_project_task.s(params).apply()
