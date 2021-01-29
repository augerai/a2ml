import botocore
import boto3
import datetime
import json
import os
import numbers
import pytest
import re
import time
import unittest

from botocore.stub import Stubber, ANY
from unittest.mock import patch

from a2ml.tasks_queue.tasks_hub_api import *
from a2ml.api.utils import fsclient
from a2ml.api.utils.s3_fsclient import BotoClient, S3FSClient
from tests.model_review.test_model_review import assert_actual_file, remove_actual_files, write_actuals

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

    def test_create_org_bucket(self):
        bucket_name = 'test-org-bucket'
        region = 'us-west-2'

        create_org_bucket({'bucket_name': bucket_name, 'region': region})

        client = BotoClient(region=region)
        assert 200 == client.head_bucket(Bucket=bucket_name)['ResponseMetadata']['HTTPStatusCode']

    def test_delete_org_bucket(self):
        bucket_name = 'test-org-bucket'
        region = 'us-west-2'

        client = S3FSClient()
        client.ensure_bucket_created(Bucket=bucket_name)

        client = BotoClient()
        client.put_object(Bucket=bucket_name, Key='dir1/key1')
        client.put_object(Bucket=bucket_name, Key='dir1/key2')
        client.put_object(Bucket=bucket_name, Key='dir2/key1')

        delete_org_bucket({'bucket_name': bucket_name})

        with pytest.raises(botocore.exceptions.ClientError, match=r"HeadBucket operation: Not Found"):
            client.head_bucket(Bucket=bucket_name)['ResponseMetadata']['HTTPStatusCode']

    def test_score_actuals_by_model_task_with_external_model(self):
        setattr(score_actuals_by_model_task, "start_time", time.time())

        hub_info, project_name, model_path = self._build_hub_info()
        options_path = os.path.join(model_path, "options.json")
        actual_date = "2020-11-16"

        remove_actual_files(model_path)
        self._write_options_file(model_path, None, "y", with_features=False)

        params = {
            "hub_info": hub_info,
            "external_model": True,
            "actual_at": "2020-11-16T14:15:53.996Z",
            "actual_date": actual_date,
            "return_count": True,
            "target_column": "y",
            "scoring": "accuracy",
            "task_type": "classification",
            "actual_columns": ["x_int", "x_double", "x_date", "x_bool", "x_str", "y", "actual"],
            "actual_records": [
                [1, 2.2, datetime.date(2020, 11, 16), True, "cat1", 0, 0],
                [1, 2.5, datetime.date(2020, 11, 17), False, "cat2", 0, 1],
            ],
        }

        with patch("a2ml.tasks_queue.tasks_hub_api.send_result_to_hub") as mock_requests:
            res = score_actuals_by_model_task(params)

            assert 0.5 == res["score"]["accuracy"]
            assert 2 == res["count"]

            saved_actuals = list(assert_actual_file(model_path, actual_date=actual_date, with_features=True))
            assert 1 == len(saved_actuals)

            (day, _, actuals) = saved_actuals[0]

            assert actual_date == str(day)
            assert 2 == len(actuals)

            options = fsclient.read_json_file(options_path)

            assert options == {
                "targetFeature": "y",
                "featureColumns": ["x_int", "x_double", "x_date", "x_bool", "x_str", "actual"],
                "originalFeatureColumns": ["x_int", "x_double", "x_date", "x_bool", "x_str", 'y', "actual"],
                "task_type": "classification",
                "scoring": "accuracy",
                "score_name": "accuracy",
                "scoreNames": ["accuracy"],
                "classification": True,
                "categoricalFeatures": ["x_date", "x_str"],
                "binaryClassification": False,
                "datasource_transforms": [[]],
            }

    def test_score_model_performance_daily_task_with_external_model(self):
        setattr(score_model_performance_daily_task, "start_time", time.time())

        hub_info, project_name, model_path = self._build_hub_info()
        date_from = datetime.date(2020, 11, 16)
        date_to = datetime.date(2020, 11, 17)
        remove_actual_files(model_path)

        params = {
            "hub_info": hub_info,
            "external_model": True,
            "date_from": str(date_from),
            "date_to": str(date_to),
        }


        actuals = self._build_actuals([date_from, date_to])
        write_actuals(model_path, actuals[date_from], with_features=True, date=date_from)
        write_actuals(model_path, actuals[date_to], with_features=False, date=date_to)
        self._write_options_file(model_path, actuals, "y")

        with patch('a2ml.tasks_queue.tasks_hub_api.send_result_to_hub') as mock_requests:
            res = score_model_performance_daily_task(params)
            assert type(res) is dict
            date_item = res[str(date_from)]
            score = date_item['scores'][date_item['score_name']]
            assert score == 0.5
            date_item = res[str(date_to)]
            score = date_item['scores'][date_item['score_name']]
            assert score == 1.0
            #assert {str(date_from): 0.5, str(date_to): 1.0} == res

    def test_distribution_chart_stats_task_with_external_model(self):
        setattr(distribution_chart_stats_task, "start_time", time.time())

        hub_info, project_name, model_path = self._build_hub_info()
        date_from = datetime.date(2020, 11, 16)
        date_to = datetime.date(2020, 11, 17)
        remove_actual_files(model_path)

        params = {
            "hub_info": hub_info,
            "external_model": True,
            "date_from": str(date_from),
            "date_to": str(date_to),
        }

        actuals = self._build_actuals([date_from, date_to])
        write_actuals(model_path, actuals[date_from], with_features=True, date=date_from)
        write_actuals(model_path, actuals[date_to], with_features=False, date=date_to)
        self._write_options_file(model_path, actuals, "y")

        with patch('a2ml.tasks_queue.tasks_hub_api.send_result_to_hub') as mock_requests:
            res = distribution_chart_stats_task(params)
            print(res)
            assert 3 == len(res)
            assert 2 == len(res[str(date_to)])
            assert "actual_y" in res[str(date_to)]
            assert "predicted_y" in res[str(date_to)]

            assert 2 == len(res['base_stat'])
            assert "actual_y" in res['base_stat']
            assert "predicted_y" in res['base_stat']

    def test_add_external_model_task(self):
        setattr(add_external_model_task, "start_time", time.time())

        hub_info, project_name, model_path = self._build_hub_info()
        options_path = os.path.join(model_path, "options.json")

        fsclient.remove_file(options_path)

        params = {
            "hub_info": hub_info,
            "target_column": "y",
            "scoring": "accuracy",
            "task_type": "classification",
        }

        with patch("a2ml.tasks_queue.tasks_hub_api.send_result_to_hub") as mock_requests:
            add_external_model_task(params)

            options = fsclient.read_json_file(options_path)

            assert options == {
                "targetFeature": "y",
                "task_type": "classification",
                "classification": True,
                "scoring": "accuracy",
                "score_name": "accuracy",
                "scoreNames": ["accuracy"],
                'binaryClassification': False,
            }

    def _build_actuals(self, dates=None):
        dates = dates or [datetime.date.today()]

        def actuals(index):
            return {
                "x1": [1.1, 1.2],
                "x2": [2.1, 2.2],
                "x3": [3.1, 3.2],
                "y": [0, 0],
                "a2ml_predicted": [0, 1 if index % 2 == 0 else 0],
            }

        return { date : actuals(index) for index, date in enumerate(dates) }


    def _build_hub_info(self):
        project_name = "external-project"

        hub_info = {
            "pipeline_id": "b7c5c4ef5a7b3a24",
            "project_name": project_name,
            "project_path": f"tmp/workspace/projects/{project_name}",
            "cluster_task_id": 144237,
        }

        model_path = os.path.join(hub_info["project_path"], "models", hub_info["pipeline_id"])
        return hub_info, project_name, model_path

    def _write_options_file(self, model_path, actuals, target_feature, with_features=True):
        feature_columns = []
        categorical_features = []

        if actuals:
            for feature, values in list(actuals.values())[0].items():
                if feature != target_feature:
                    feature_columns.append(feature)
                    if not isinstance(values[0], numbers.Number):
                        categorical_features.append(feature)

        options = {
            "targetFeature": target_feature,
            "task_type": "classification",
            "classification": True,
            "scoring": "accuracy",
            "score_name": "accuracy",
            "scoreNames": ["accuracy"],
        }

        if with_features:
            options["featureColumns"] = feature_columns
            options["categoricalFeatures"] = categorical_features
            options["datasource_transforms"] = [[]]

        fsclient.write_json_file(os.path.join(model_path, "options.json"), options)

@pytest.mark.parametrize("expires_in", [1800, None])
@pytest.mark.parametrize("method", ["GET", "PUT"])
@pytest.mark.parametrize("with_path", [False, True])
def test_presign_s3_url_task_get_put(expires_in, method, with_path):
    setattr(presign_s3_url_task, "start_time", time.time())

    bucket = "auger-mt-org-test"
    key = "workspace/projects/alex-mt-test-exp/files/iris-d336e4.csv"
    client = S3FSClient()
    client.ensure_bucket_created(bucket)

    params = {
        "method": method,
        "expires_in": expires_in,
    }

    if with_path:
        params["path"] = f"s3://{bucket}/{key}"
    else:
        params["bucket"] = bucket
        params["key"] = key

    with patch("a2ml.tasks_queue.tasks_hub_api.send_result_to_hub") as mock_requests:
        res = presign_s3_url_task(params)

        assert isinstance(res, str)
        assert f"/{bucket}" in res

        if expires_in:
            assert f"X-Amz-Expires={expires_in}" in res
        else:
            assert f"X-Amz-Expires=3600" in res , "expires_in should be 3600 by default"

@pytest.mark.parametrize("expires_in", [1800, None])
@pytest.mark.parametrize("max_content_length", [1048576, None])
@pytest.mark.parametrize("with_path", [False, True])
def test_presign_s3_url_task_post(expires_in, max_content_length, with_path):
    setattr(presign_s3_url_task, "start_time", time.time())

    bucket = "auger-mt-org-test"
    key = "workspace/projects/alex-mt-test-exp/files/iris-d336e4.csv"
    client = S3FSClient()
    client.ensure_bucket_created(bucket)

    params = {
        "method": "POST",
        "expires_in": expires_in,
        "max_content_length": max_content_length,
    }

    if with_path:
        params["path"] = f"s3://{bucket}/{key}"
    else:
        params["bucket"] = bucket
        params["key"] = key

    with patch("a2ml.tasks_queue.tasks_hub_api.send_result_to_hub") as mock_requests:
        res = presign_s3_url_task(params)

        assert isinstance(res, dict)
        assert len(res) == 2
        assert isinstance(res["url"], str)
        assert f"/{bucket}" in res["url"]

        fields = res["fields"]

        assert 200 == fields["success_action_status"]
        assert key == fields["key"]

# Looks like it's not possible or very complex to create IAM role in Minio
# So mock here
@pytest.mark.parametrize("with_path", [False, True])
@patch("a2ml.api.utils.s3_fsclient.BotoClient._build_client")
def test_presign_s3_url_task_for_multipart_upload(build_client_mock, monkeypatch, with_path):
    role_arn = "some_role_arn-12312233434"
    aws_s3_host = "s3.amazonaws.com"
    setattr(presign_s3_url_task, "start_time", time.time())
    monkeypatch.setenv("AWS_ROLE_ARN", role_arn)

    sts_client = boto3.client('sts')
    sts_stubber = Stubber(sts_client)
    s3_client = boto3.client('s3')
    s3_client._endpoint = botocore.endpoint.Endpoint(f"https://{aws_s3_host}", "s3", None)

    build_client_mock.side_effect = [s3_client, sts_client]

    assume_role_response = {
        "Credentials": {
            "AccessKeyId": "some-strong-secret-a",
            "SecretAccessKey": "some-strong-secret-s",
            "SessionToken": "some-strong-secret-t",
            "Expiration": datetime.datetime.now(),
        }
    }

    expires_in = 1800

    expected_params = {
        'RoleArn': role_arn,
        'DurationSeconds': expires_in,
        'Policy': ANY,
        'RoleSessionName': ANY,
    }

    sts_stubber.add_response('assume_role', assume_role_response, expected_params)

    with sts_stubber:
        bucket = "auger-mt-org-test"
        key = "workspace/projects/alex-mt-test-exp/files/iris-d336e4.csv"

        params = {
            "multipart": True,
            "expires_in": expires_in,
        }

        if with_path:
            params["path"] = f"s3://{bucket}/{key}"
        else:
            params["bucket"] = bucket
            params["key"] = key

        with patch("a2ml.tasks_queue.tasks_hub_api.send_result_to_hub") as mock_requests:
            res = presign_s3_url_task(params)

            assert isinstance(res, dict)
            assert len(res) == 3
            assert bucket == res["bucket"]
            assert key == res["key"]
            assert isinstance(res["config"], dict)

            assert assume_role_response["Credentials"]["AccessKeyId"] == res["config"]["access_key"]
            assert assume_role_response["Credentials"]["SecretAccessKey"] == res["config"]["secret_key"]
            assert assume_role_response["Credentials"]["SessionToken"] == res["config"]["security_token"]

            assert "endpoint" in res["config"]
            assert "port" in res["config"]
            assert "use_ssl" in res["config"]

            assert None == res["config"]["endpoint"]

