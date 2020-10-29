import os
import pytest
import unittest
import json

from a2ml.tasks_queue.tasks_hub_api import *

# pytestmark = pytest.mark.usefixtures('config_context')

class TestTasksHubApiAuger(unittest.TestCase):

    @pytest.mark.skip(reason='run it locally')
    def test_import_data(self):
        params = {
            'provider': "azure",
            'hub_info': {
                'project_file_id': '2719',
                'project_name': 'a2ml_azure_adult_4'
            },
            'url': '/Users/evgenyvovchenko/Projects/auger-experiments/files/adult.data.csv',
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
            'start_monitor_evaluate': False,
            'hub_info': {
                'experiment_id': 'bb29d41a246f601b',
                'project_id': '820',
                'experiment_session_id': '010def8e3cb89236',
                'experiment_name': 'adult-data-csv'
            },
            'provider_info': {
                'azure' : {
                    'project_file':{
                        'url': 'adult.data.csv'
                    },
                    'project':{
                        'name': 'a2ml_azure_adult_3',
                        'cluster': {
                            'name': 'cpucluster',
                            'min_nodes': 0,
                            'max_nodes': 2,
                            'type': 'STANDARD_D2_V2'
                        }
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
        from a2ml.tasks_queue.tasks_hub_api import _get_leaderboad, monitor_evaluate_task

        params = {
            'provider': "azure",
            'hub_info': {
                'experiment_id': '6707c6082dd7b08f',
                'project_id': '851',
                'experiment_session_id': 'd0592e467e322eaf'
            },
            'provider_info': {
                'azure' : {
                    'project':{
                        'name': 'options-a2ml'
                    },
                    'experiment': {
                        'name': 'options-a2ml',
                    },
                    'experiment_session': {
                        'id': 'AutoML_adfc1a28-2963-4fba-821c-503786ad5c7b',
                    },
                }
            }
        }
        #monitor_evaluate_task(params)
        res = _get_leaderboad(params)
        print(res)
        
        self.assertTrue(res)
        self.assertTrue(res[0]['uid'])
        self.assertTrue(res[0]['all_scores'])
        self.assertTrue(res[0]['algorithm_params'])


    @pytest.mark.skip(reason='run it locally')
    def test_stop_evaluate(self):
        params = {
            'provider': "azure",
            'provider_info': {
                'azure' : {
                    'project':{
                        'name': 'a2ml_azure_adult_3'
                    },
                    'experiment': {
                        'name': '123_adult_data_csv',
                    },
                    'experiment_session': {
                        'id': 'AutoML_54a4538c-b9d7-4f56-91f4-775be7f02c75',
                    },
                }
            }
        }
        #monitor_evaluate_task(params)
        res = stop_evaluate_task(params)
        print(res)
        
        self.assertTrue(res)

    @pytest.mark.skip(reason='run it locally')
    def test_update_cluster_config(self):
        params = {
            'provider': "azure",
            'provider_info': {
                'azure' : {
                    'project':{
                        'name': 'a2mlworkspacedev'
                    },
                }
            },
            'clusters': [
                {
                    "name": "free",
                    "type": "STANDARD_D3_V2",
                    "max_nodes": 3,
                    "min_nodes": 0
                }            
                # {
                #     'name': 'new-test-2',
                #     'min_nodes': 0,
                #     'max_nodes': 4,
                #     #'vm_size': 'STANDARD_D3_V2',
                #     'type': 'STANDARD_D2_V2',#'STANDARD_D3_V2',
                #     'idle_seconds_before_scaledown': 100
                # }
            ]
        }
        res = update_cluster_config_task(params)
        print(res)
        
        #self.assertTrue(res)

    @pytest.mark.skip(reason='run it locally')
    def test_delete_actuals_task(self):
        params = {
            'provider': "azure",

            'with_predictions': True,
            #'begin_date': "2020-08-18",
            #'end_date': "2020-08-18",

            'hub_info': {
                'pipeline_id': 'AutoML_af67d4a6-3feb-4835-82a6-c545a9fea973_2',
                'project_path': '/Users/evgenyvovchenko/Projects/auger-experiments/a2ml_azure_adult_3',
            },
        }
        res = delete_actuals_task(params)
        print(res)

        # self.assertTrue("azure" in res)
        # self.assertTrue(res["azure"]["result"])

    @pytest.mark.skip(reason='run it locally')
    def test_deploy_model(self):
        params = {
            'provider': "azure",
            'model_id': 'AutoML_2186b1cb-c97b-4a49-9bcf-e98098fdfa22_5',
            'support_review_model': True,

            'hub_info': {
                'project_name': 'bike_regr',
                'project_path': 'tests/tmp',
                # 'experiment_id': 'bb29d41a246f601b',
                # 'experiment_session_id': '010def8e3cb89236'
                'experiment_session': {
                    'model_settings':{
                        'evaluation_options': {}
                    }
                    # 'id': 'AutoML_22f2274b-9596-4912-b86b-9799df81d41b',
                },                
            },

            'provider_info': {
                'azure' : {
                    'project':{
                        "deploy_cluster": {
                            'type': 'aks',
                            'memory_gb': 2,
                            'cpu_cores': 1,
                            'compute_target': 'a2ml_aks'
                        }                        
                    },
                    'experiment': {
                        'name': 'bike-day-sample-',
                    },
                }
            }
        }
        res = deploy_model_task(params)
        #print(res)

        self.assertTrue("azure" in res)
        self.assertTrue(res["azure"]["result"])

    def _get_predict_params(self):
        return {
            'provider': "azure",

            'model_id': 'AutoML_22f2274b-9596-4912-b86b-9799df81d41b_0',
            'path_to_predict':'tests/fixtures/adult.data_test.csv',

            'hub_info': {
                'project_path': 'tests/tmp',
                'experiment_id': 'bb29d41a246f601b',
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

    @pytest.mark.skip(reason='run it locally')
    def test_predict(self):
        params = self._get_predict_params()
        res = predict_by_model_task(params)
        print(res)

        self.assertTrue(len(res["predicted"])>0)

    @pytest.mark.skip(reason='run it locally')
    def test_predict_json(self):
        params = self._get_predict_params()
        params['json_result']=True
        params['count_in_result']=True
        params['threshold'] = 0.7

        res = predict_by_model_task(params)
        print(res)

        self.assertTrue(len(res["predicted"])>0)

        predicted = json.loads(res["predicted"])
        print(predicted.keys())

        self.assertEqual(predicted['columns'], ["age","workclass","fnlwgt","education","education-num","marital-status","occupation","relationship","race","sex","capital-gain","capital-loss","hours-per-week","native-country","income","proba_0","proba_1"] )
        self.assertEqual(len(predicted['data']), 7)
