import boto3
import botocore
import json
import os
import re

from a2ml.tasks_queue.tasks_api import *
from a2ml.api.utils.context import Context
from tests.vcr_helper import vcr

class TestTasks(object):
    def auger_yaml(self):
        return {
            "py/object": "a2ml.api.utils.config.SerializableConfigYaml",
            "py/state": {
                "filename": "/Users/alex/soft/a2ml/tmp/my_app/auger.yaml",
                "yaml": '''
                    dataset:
                    experiment:
                        name:
                        experiment_session_id:
                        time_series:
                        label_encoded: []
                        metric: accuracy
                    cluster:
                        type: standard
                        min_nodes: 2
                        max_nodes: 2
                        stack_version: experimental
                    '''
            }
        }

    def azure_yaml(self):
        return {
            "py/object": "a2ml.api.utils.config.SerializableConfigYaml",
            "py/state": {
                "filename": "/Users/alex/soft/a2ml/tmp/my_app/azure.yaml",
                "yaml": '''
                    dataset:
                    experiment:
                      name:
                      run_id:
                      metric: AUC_weighted

                      cluster:
                      region: eastus2
                      min_nodes: 0
                      max_nodes: 2
                      type: STANDARD_D2_V2
                    '''
            }
        }

    def config_yaml(self):
        return {
            "py/object": "a2ml.api.utils.config.SerializableConfigYaml",
            "py/state": {
                "filename": "/Users/alex/soft/a2ml/tmp/my_app/config.yaml",
                "yaml": '''
                    use_server: true
                    server_endpoint: http://localhost:8000
                    debug: true

                    name: my_app
                    providers: auger
                    source: /Users/alex/data-sets/iris.csv
                    exclude:
                    target: species
                    model_type: classification

                    budget: 300000
                    experiment:
                        cross_validation_folds: 5
                        max_total_time: 60
                        max_eval_time: 5
                        max_n_trials: 10
                        use_ensemble: true

                        name: iris-3.csv-experiment
                        experiment_session_id: 609ece51c7e31f7b
                        dataset: iris-3.csv
                    '''
            }
        }

    def google_yaml(self):
        return {
            "py/object": "a2ml.api.utils.config.SerializableConfigYaml",
            "py/state": {
                "filename": "/Users/alex/soft/a2ml/tmp/my_app/google.yaml",
                "yaml": '''
                    project:
                    experiment:
                      metric: MINIMIZE_MAE
                    cluster:
                      region: us-central1
                    gsbucket:
                    '''
            }
        }

    def context(self):
        return {
            "_runs_on_server": False,
            "config": {
                "name": "config",
                "parts": {
                    "is_loaded": True,
                    "part_names": [
                        "config",
                        "auger",
                        "azure",
                        "google"
                    ],
                    "parts": {
                        "auger": self.auger_yaml(),
                        "azure": self.azure_yaml(),
                        "config": self.config_yaml(),
                        "google": self.google_yaml(),
                    },
                    "py/object": "a2ml.api.utils.config.ConfigParts"
                },
                "path": None,
                "py/object": "a2ml.api.utils.config.Config",
                "runs_on_server": False
            },
            "credentials": {
                "api_url": "https://app-staging.auger.ai",
                "organization": "mt-org",
                "token": "secret",
                "username": "alex@auger.ai"
            },
            "debug": True,
            "name": "[config] ",
            "notificator": None,
            "py/object": "a2ml.api.utils.context.Context",
            "request_id": None
        }

    def params(self):
        return {
            'project_name': 'my_app',
            'args': [],
            'kwargs': {},
            '_request_id': 'ea12ed33-a94f-4d45-ab78-85735c388632',
            'context': json.dumps(self.context())
        }

    def s3_resource(self):
        return boto3.resource('s3', endpoint_url=os.environ.get('S3_ENDPOINT_URL', None))

    def review_bucket(self):
        return self.s3_resource().Bucket('review-data')

    def clear_bucket(self, bucket):
        try:
            for obj in bucket.objects.filter(Prefix='/'):
                obj.delete()

        except botocore.client.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                pass
            else:
                raise e

    def list_s3_files(self, bucket):
        res = []
        for obj in bucket.objects.filter(Prefix='/'):
            res.append(obj.key)

        return res

    @vcr.use_cassette('predict/valid.yaml')
    def test_predict(self):
        review_bucket = self.review_bucket()
        self.clear_bucket(review_bucket)

        params = self.params()
        path = 's3://sample-bucket/workspace/projects/a2ml-app/files/iris_for_predict.csv'
        params['args'] = [path, '555777999', None, False]

        res = predict_model_task.apply([params]).result
        assert isinstance(res, dict)
        assert res['response']['auger']['result'] == True, res['response']['auger']['data']

        files = self.list_s3_files(review_bucket)
        assert isinstance(files, list)
        assert len(files) == 1

        assert re.match(
            '\/auger\/models\/555777999\/predictions\/\d{4}-\d{2}-\d{2}_[0-9a-f\-]+_results.pkl.gz',
            files[0]
        )
