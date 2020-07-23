import re

from a2ml.tasks_queue.tasks_api import *
from a2ml.api.utils.context import Context
from tests.tasks_queue.base_test import BaseTest
from tests.vcr_helper import vcr
from unittest.mock import ANY

# For record cassetes run
# make docker-up
# set credentials in base_test.build_context
# AWS_ACCESS_KEY_ID=secret AWS_SECRET_ACCESS_KEY=strongsecret S3_ENDPOINT_URL=http://localhost:9000 pytest tests/tasks_queue/test_tasks_api_auger.py

# Revert credentials change back in base_test.build_context after recording

class TestTasksApiAuger(BaseTest):
    def assert_result(self, res, expected_result, expected_data, no_provider_in_result=False):
        assert isinstance(res, dict)

        if no_provider_in_result:
            response = res['response']
        else:
            response = res['response']['auger']

        assert response['result'] == expected_result, response['data']
        assert response['data'] == expected_data

    @vcr.use_cassette('auger/new/valid.yaml')
    def test_new_success(self):
        params = self.params('auger', 'new-project-name')
        res = new_project_task.apply(params).result
        self.assert_result(res, True, {'created': 'new-project-name'})

    @vcr.use_cassette('auger/import/valid.yaml')
    def test_import_valid(self):
        params = self.params('auger')
        res = import_data_task.apply(params).result
        self.assert_result(res, True, {'created': 'iris-13.csv'})

    @vcr.use_cassette('auger/train/valid.yaml')
    def test_train_valid(self):
        params = self.params('auger')
        res = train_task.apply(params).result
        self.assert_result(res, True, {'experiment_name': ANY, 'session_id': ANY})

    @vcr.use_cassette('auger/evaluate/valid.yaml')
    def test_evaluate_valid(self):
        params = self.params('auger', '29654979bf8a1877')
        res = evaluate_task.apply(params).result
        self.assert_result(res, True, 
            {'leaderboard': ANY, 'run_id': '29654979bf8a1877', 
            'status': 'completed', 'provider_status': 'completed', 'trials_count': 19})

    @vcr.use_cassette('auger/deploy/valid.yaml')
    def test_deploy_valid(self):
        params = self.params('auger', '390955D2AB984D7')
        res = deploy_task.apply(params).result
        self.assert_result(res, True, {'model_id': '390955D2AB984D7'}, no_provider_in_result=True)

    @vcr.use_cassette('auger/project/list_valid.yaml')
    def test_project_list_valid(self):
        params = self.params('auger')
        res = list_projects_task.apply(params).result
        self.assert_result(res, True, {'projects': ANY})

    @vcr.use_cassette('auger/project/delete_valid.yaml')
    def test_project_delete_valid(self):
        params = self.params('auger', 'new-project-name')
        res = delete_project_task.apply(params).result
        self.assert_result(res, True, {'deleted': 'new-project-name'})

    @vcr.use_cassette('auger/dataset/list_valid.yaml')
    def test_dataset_list_valid(self):
        params = self.params('auger')
        res = list_datasets_task.apply(params).result
        self.assert_result(res, True, {'datasets': ANY})

    @vcr.use_cassette('auger/dataset/delete_valid.yaml')
    def test_dataset_delete_valid(self):
        params = self.params('auger', 'iris-13.csv')
        res = delete_dataset_task.apply(params).result
        self.assert_result(res, True, {'deleted': 'iris-13.csv'})

    @vcr.use_cassette('auger/experiment/history_valid.yaml')
    def test_experiment_history_valid(self):
        params = self.params('auger')
        res = history_experiment_task.apply(params).result
        self.assert_result(res, True, {'history': ANY})

    @vcr.use_cassette('auger/experiment/leaderboard_valid.yaml')
    def test_experiment_leaderboard_valid(self):
        params = self.params('auger', 'a6bc4bdb6607e7c2')
        res = leaderboard_experiment_task.apply(params).result
        self.assert_result(res, True, {'leaderboard': ANY, 'run_id': 'a6bc4bdb6607e7c2', 
            'status': 'completed', 'provider_status': 'completed', 'trials_count': 34})

    @vcr.use_cassette('auger/experiment/list_valid.yaml')
    def test_experiment_list_valid(self):
        params = self.params('auger')
        res = list_experiments_task.apply(params).result
        self.assert_result(res, True, {'experiments': ANY})

    @vcr.use_cassette('auger/predict/valid.yaml')
    def test_predict_success(self):
        params = self.params(
            'auger',
            's3://sample-bucket/workspace/projects/a2ml-app/files/iris_for_predict.csv',
            '2B702A5511A44E3',
            None,
            False
        )

        res = predict_model_task.apply(params).result
        self.assert_result(res, True, {'predicted': ANY}, no_provider_in_result=True)

    @vcr.use_cassette('auger/predict/invalid_model.yaml')
    def test_predict_failure_model_status(self):
        params = self.params(
            'auger',
            's3://sample-bucket/workspace/projects/a2ml-app/files/iris_for_predict.csv',
            'BF8BDC3CD21648A',
            None,
            False
        )

        res = predict_model_task.apply(params).result
        self.assert_result(res, False, 'Pipeline BF8BDC3CD21648A is not ready...', no_provider_in_result=True)

