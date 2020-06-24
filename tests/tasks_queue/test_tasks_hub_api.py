import os
import pytest
import unittest

from a2ml.tasks_queue.tasks_hub_api import *

pytestmark = pytest.mark.usefixtures('config_context')

class TestTasksHubApiAuger(unittest.TestCase):

    @pytest.mark.skip(reason='run it locally')
    def test_import_data(self):
        params = {
            'provider': "azure",
            'augerInfo': {
                'project_file_id': '2719',
            },
            'url': '/Users/evgenyvovchenko/Projects/auger-experiments/files/adult.data.csv',
            'provider_info': {
                'azure' : {
                    'project':{
                        'name': 'a2ml_azure_adult_3'
                    },
                }
            }
        }
        res = import_data_task(params)
        print(res)

        self.assertTrue("azure" in res)
        self.assertTrue(res["azure"]["result"])
        self.assertEqual(res["azure"]["data"]['dataset'], 'adult.data.csv')

    @pytest.mark.skip(reason='run it locally')
    def test_evaluate_start(self):
        params = {
            'provider': "azure",
            'augerInfo': {
                'experiment_id': 'bb29d41a246f601b',
                'project_id': '820',
                'experiment_session_id': '010def8e3cb89236'
            },
            'provider_info': {
                'azure' : {
                    'project_file':{
                        'url': 'adult.data.csv'
                    },
                    'project':{
                        'name': 'a2ml_azure_adult_3'
                    },
                    'experiment': {
                        'name': 'adult-data-csv',
                    },
                    'cluster': {
                        'name': 'cpucluster',
                        'min_nodes': 0,
                        'max_nodes': 2,
                        'type': 'STANDARD_D2_V2'
                    }
                }
            }
        }
        res = evaluate_start_task(params)
        print(res)

        self.assertTrue("azure" in res)
        self.assertTrue(res["azure"]["result"])
        self.assertEqual(res["azure"]["data"]['experiment_name'], 'adult-data-csv')
        self.assertTrue(res["azure"]["data"]['run_id'].startswith("AutoML_"))


    @pytest.mark.skip(reason='run it locally')
    def test_evaluate_monitor(self):
        from a2ml.tasks_queue.tasks_hub_api import _get_leaderboad_trials

        params = {
            'provider': "azure",
            'augerInfo': {
                'experiment_id': 'bb29d41a246f601b',
                'project_id': '820',
                'experiment_session_id': '010def8e3cb89236'
            },
            'provider_info': {
                'azure' : {
                    'project':{
                        'name': 'a2ml_azure_adult_3'
                    },
                    'experiment': {
                        'name': 'adult-data-csv',
                    },
                    'experiment_session': {
                        'id': 'AutoML_22f2274b-9596-4912-b86b-9799df81d41b',
                    },
                }
            }
        }
        res = _get_leaderboad_trials(params)
        self.assertTrue(res)
        self.assertTrue(res[0]['uid'])
        self.assertTrue(res[0]['all_scores'])
        self.assertTrue(res[0]['algorithm_params'])

