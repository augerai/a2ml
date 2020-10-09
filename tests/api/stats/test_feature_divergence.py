import datetime
import json
import unittest

from a2ml.api.stats.feature_divergence import FeatureDivergence
from a2ml.api.utils import fsclient

class TestFeatureDivergence(unittest.TestCase):
    def test_build_and_save_model(self):
        fd = FeatureDivergence(self._load_metric_task_params())
        res = fd.build_and_save_model()

        self.assertIsInstance(res, str)

        model = fsclient.load_object_from_file(res)
        self.assertIsInstance(model, FeatureDivergence.DensityEstimatorPerFeature)

    def test_score_divergence_daily(self):
        fd = FeatureDivergence(self._load_metric_task_params())

        model_path = self._project_path() + '/models/F6F741544E9A468'
        date_from = datetime.date(2020, 10, 7)
        date_to = datetime.date(2020, 10, 8) # divergence should be lesser than day before
        res = fd.score_divergence_daily(model_path, date_from, date_to, divergence_model_name='test_density_model.pkl')

        self.assertIsInstance(res, dict)
        self.assertIn(str(date_from), res)
        self.assertIn(str(date_to), res)

        self.assertIsInstance(res[str(date_to)], dict)
        self.assertIn('sepal_length', res[str(date_to)])
        self.assertIn('sepal_width', res[str(date_to)])
        self.assertIn('petal_length', res[str(date_to)])
        self.assertIn('petal_width', res[str(date_to)])
        self.assertIn('species', res[str(date_to)])

        self.assertIsInstance(res[str(date_to)]['petal_width'], float)
        self.assertGreater(res[str(date_to)]['petal_width'], res[str(date_from)]['petal_width'])

    def _project_path(self):
        return 'tests/fixtures/test_feature_divergence'

    def _load_metric_task_params(self):
        path = self._project_path() + '/task_params.json'

        res = {}

        with open(path, 'r') as f:
            res = json.load(f)

        hub_info = res['hub_info']
        hub_info['experiment_id'] = '112233'
        hub_info['experiment_session_id'] = 'AABBCCDD'
        hub_info['project_path'] = 'tests/fixtures/test_feature_divergence'

        evaluation_options = hub_info['experiment_session']['model_settings']['evaluation_options']
        evaluation_options['data_path'] = self._project_path() + '/iris.csv'

        return res
