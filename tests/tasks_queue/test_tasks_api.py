import re

from a2ml.tasks_queue.tasks_api import *
from a2ml.api.utils.context import Context
from tests.tasks_queue.base_test import BaseTest
from tests.vcr_helper import vcr

class TestTasks(BaseTest):
    @vcr.use_cassette('predict/valid.yaml')
    def test_predict_success(self):
        review_bucket = self.review_bucket()
        self.clear_bucket(review_bucket)

        params = self.params(
            's3://sample-bucket/workspace/projects/a2ml-app/files/iris_for_predict.csv',
            '555777999',
            None,
            False
        )

        res = predict_model_task.apply(params).result
        assert isinstance(res, dict)
        assert res['response']['auger']['result'] == True, res['response']['auger']['data']

        files = self.list_s3_files(review_bucket)
        assert isinstance(files, list)
        assert len(files) == 1

        assert re.match(
            '\/auger\/models\/555777999\/predictions\/\d{4}-\d{2}-\d{2}_[0-9a-f\-]+_results.pkl.gz',
            files[0]
        )

    @vcr.use_cassette('predict/invalid_model.yaml')
    def test_predict_failure_model_status(self):
        review_bucket = self.review_bucket()
        self.clear_bucket(review_bucket)

        params = self.params(
            's3://sample-bucket/workspace/projects/a2ml-app/files/iris_for_predict.csv',
            '000111222',
            None,
            False
        )

        res = predict_model_task.apply(params).result

        assert isinstance(res, dict)
        assert res['response']['auger']['result'] == False
        assert res['response']['auger']['data'] == 'Pipeline 000111222 is not ready...'

