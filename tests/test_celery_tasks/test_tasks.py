import os
import pytest

from a2ml.tasks_queue.tasks_api import *

pytestmark = pytest.mark.usefixtures('config_context')


class TestTasks(object):

    @pytest.mark.skip(reason='run it locally')
    def test_import(self):
        params = {
            'provider': 'auger',
            'debug_log': True
        }

        execute_tasks(import_data_task, params)

	#@pytest.mark.skip(reason='run it locally')        	
    def test_import_s3(self):
        params = {
            'provider': 'auger',
            'debug_log': True,
            'source_path': 's3://auger-demo-datasets/a2ml_app/adult.data.csv'
        }

        execute_tasks(import_data_task, params)
