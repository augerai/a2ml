import datetime
import json
import unittest

from a2ml.api.stats.feature_divergence import FeatureDivergence
from a2ml.api.utils import fsclient

class TestFeatureDivergence(unittest.TestCase):
    def test_build_and_save_model(self):
        fd = FeatureDivergence(self._load_task_params())
        res = fd.build_and_save_model(divergence_model_name='density_model.pkl')

        self.assertIsInstance(res, str)

        model = fsclient.load_object_from_file(res)
        self.assertIsInstance(model, FeatureDivergence.DensityEstimatorPerFeature)

    def test_score_divergence_daily(self):
        fd = FeatureDivergence(self._load_task_params())

        date_from = datetime.date(2020, 10, 7)
        date_to = datetime.date(2020, 10, 8) # divergence should be lesser than day before
        res = fd.score_divergence_daily(date_from, date_to, divergence_model_name='test_density_model.pkl')

        self.assertIsInstance(res, dict)
        self.assertIn('divergence', res)
        self.assertIn('importance', res)

        importance = res['importance']
        self.assertIsInstance(importance, dict)
        self.assertIn('sepal_length', importance)
        self.assertIn('sepal_width', importance)
        self.assertIn('petal_length', importance)
        self.assertIn('petal_width', importance)
        self.assertNotIn('species', importance)

        divergence = res['divergence']
        self.assertIsInstance(divergence, dict)
        self.assertIn(str(date_from), divergence)
        self.assertIn(str(date_to), divergence)

        self.assertIsInstance(divergence[str(date_to)], dict)
        self.assertIn('sepal_length', divergence[str(date_to)])
        self.assertIn('sepal_width', divergence[str(date_to)])
        self.assertIn('petal_length', divergence[str(date_to)])
        self.assertIn('petal_width', divergence[str(date_to)])
        self.assertIn('species', divergence[str(date_to)])

        self.assertIsInstance(divergence[str(date_to)]['petal_width'], float)
        self.assertTrue(divergence[str(date_to)]['petal_width'] < divergence[str(date_from)]['petal_width'])

    def test_score_divergence_daily_top_n(self):
        fd = FeatureDivergence(self._load_task_params())

        date_from = datetime.date(2020, 10, 7)
        date_to = datetime.date(2020, 10, 8) # divergence should be lesser than day before
        res = fd.score_divergence_daily(date_from, date_to, divergence_model_name='test_density_model.pkl', top_n=2)

        self.assertIsInstance(res, dict)
        self.assertIn('divergence', res)
        self.assertIn('importance', res)

        importance = res['importance']
        self.assertIsInstance(importance, dict)
        self.assertIn('petal_length', importance)
        self.assertIn('petal_width', importance)
        self.assertNotIn('sepal_length', importance)
        self.assertNotIn('sepal_width', importance)
        self.assertNotIn('species', importance)

        divergence = res['divergence']
        self.assertIsInstance(divergence, dict)
        self.assertIn(str(date_from), divergence)
        self.assertIn(str(date_to), divergence)

        self.assertIsInstance(divergence[str(date_to)], dict)
        self.assertIn('petal_length', divergence[str(date_to)])
        self.assertIn('petal_width', divergence[str(date_to)])
        self.assertNotIn('sepal_length', divergence[str(date_to)])
        self.assertNotIn('sepal_width', divergence[str(date_to)])
        self.assertNotIn('species', divergence[str(date_to)])

        self.assertIsInstance(divergence[str(date_to)]['petal_width'], float)
        self.assertTrue(divergence[str(date_to)]['petal_width'] < divergence[str(date_from)]['petal_width'])

    def _project_path(self):
        return 'tests/fixtures/test_feature_divergence'

    def _load_task_params(self):
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
