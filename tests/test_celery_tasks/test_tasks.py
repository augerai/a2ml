import os
import pytest

from a2ml.tasks_queue.tasks_api import *

pytestmark = pytest.mark.usefixtures('config_context')


class TestTasks(object):

    @pytest.mark.skip(reason='run it locally')
    def test_import(self):
        params = {
            'provider': 'auger',
            'debug_log': True,
            'project_name': 'cli-integration-test'
        }

        execute_tasks(import_data_task, params)

	@pytest.mark.skip(reason='run it locally')
    def test_import_s3(self):
        params = {
            'provider': 'auger',
            'debug_log': True,
			'project_name': 'new-project-test-s3-5',
            #'source_path': 's3://auger-demo-datasets/a2ml_app/adult.data.csv'
        }

        execute_tasks(import_data_task, params)

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

        execute_tasks(new_project_task, params)

	@pytest.mark.skip(reason='run it locally')
    def test_new_project_s3(self):
        params = {
            'providers': ['auger', 'azure'],
            'debug_log': True,
			'project_name': 'new-project-test-s3-5',
            'source_path': 's3://auger-demo-datasets/a2ml_app/adult.data.csv',
            'target': 'income',
            'model_type': 'classification'
        }

        execute_tasks(new_project_task, params)
