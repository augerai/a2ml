import boto3
import botocore
import json
import os


class BaseTest(object):
    def params(self, provider='auger', *args, **kwargs):
        return [{
            'provider': provider,
            'project_name': 'my_app',
            'args': args,
            'kwargs': kwargs,
            '_request_id': 'ea12ed33-a94f-4d45-ab78-85735c388632',
            'context': json.dumps(self.build_context())
        }]

    def s3_resource(self):
        return boto3.resource('s3', endpoint_url=os.environ.get('S3_ENDPOINT_URL', None))

    # def review_bucket(self):
    #     return self.s3_resource().Bucket('review-data')

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

    def auger_yaml(self):
        return {
            "py/object": "a2ml.api.utils.config.SerializableConfigYaml",
            "py/state": {
                "filename": "/Users/alex/soft/a2ml/tmp/my_app/auger.yaml",
                "yaml": '''
                    dataset: iris-13.csv
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
                    source: tests/fixtures/iris.csv
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

                        name: a87e-loans-603-b-4-be-4-a-1-ab-4-e-71-a-8-f-2-8-babd-1946-f-53-csv-gz
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

    def build_context(self):
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
            "debug": False,
            "name": "[config] ",
            "notificator": None,
            "py/object": "a2ml.api.utils.context.Context",
            "request_id": None
        }
