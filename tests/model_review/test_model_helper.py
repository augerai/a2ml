import pytest
import unittest
import os
import numpy as np
import json

from a2ml.api.utils import fsclient
from a2ml.api.utils.dataframe import DataFrame
from a2ml.api.model_review.model_helper import ModelHelper


class TestModelHelper(unittest.TestCase):

    def test_preprocess_target(self):
        model_path = 'tests/fixtures/test_predict_by_model/iris'

        y_true, target_categoricals = ModelHelper.preprocess_target(model_path,
            records=[["setosa"], ["versicolor"], ["virginica"], ["setosa"], ["versicolor"], ["virginica"]],
            features=["species"]
        )
        self.assertEqual(list(y_true), [0, 1, 2, 0, 1, 2])
        self.assertEqual(target_categoricals, {'species': {'categories': ['setosa', 'versicolor', 'virginica']}})

    def test_calculate_scores(self):
        model_path = 'tests/fixtures/test_predict_by_model/iris'
        options = fsclient.read_json_file(os.path.join(model_path, "options.json"))
        options['score_top_count'] = True

        y_test, _ = ModelHelper.preprocess_target(model_path,
            records=[["setosa"], ["versicolor"], ["virginica"], ["setosa"], ["versicolor"], ["virginica"]],
            features=["species"]
        )
        y_pred, _ = ModelHelper.preprocess_target(model_path,
            records=[["setosa"], ["versicolor"], ["versicolor"], ["setosa"], ["versicolor"], ["virginica"]],
            features=["species"]
        )

        scores = ModelHelper.calculate_scores(options, y_test=y_test, y_pred=y_pred)
        self.assertEqual(len(scores), len(options['scoreNames']))
        self.assertTrue(scores['accuracy']>0.8)

    def test_calculate_scores_binary(self):
        model_path = 'tests/fixtures/test_predict_by_model/credit-g'
        options = fsclient.read_json_file(os.path.join(model_path, "options.json"))

        y_test, _ = ModelHelper.preprocess_target(model_path,
            records=[["bad"], ["bad"], ["good"], ["good"], ["bad"], ["good"]],
            features=["class"]
        )
        y_pred, _ = ModelHelper.preprocess_target(model_path,
            records=[["bad"], ["good"], ["good"], ["bad"], ["bad"], ["good"]],
            features=["class"]
        )

        scores = ModelHelper.calculate_scores(options, y_test=y_test, y_pred=y_pred)
        self.assertEqual(len(scores), len(options['scoreNames'])+4)
        self.assertTrue(scores['accuracy']>0.6)
        self.assertTrue(scores['FP']==1)
        self.assertTrue(scores['TN']==2)
        self.assertTrue(scores['FN']==1)
        self.assertTrue(scores['TP']==2)

    def test_calculate_scores_regression(self):
        model_path = 'tests/fixtures/test_predict_by_model/bike'
        options = fsclient.read_json_file(os.path.join(model_path, "options.json"))

        y_test, _ = ModelHelper.preprocess_target(model_path,
            records=[[100], [0], [34], [88], [44], [1]],
            features=["cnt"]
        )
        y_pred, _ = ModelHelper.preprocess_target(model_path,
            records=[[0], [100], [35], [80], [40], [23]],
            features=["cnt"]
        )

        scores = ModelHelper.calculate_scores(options, y_test=y_test, y_pred=y_pred)
        assert scores['mae_over'] >= 41
        assert scores['mae_under'] >= 37

    def test_calculate_scores_regression_1(self):
        model_path = 'tests/fixtures/test_predict_by_model/bike'
        options = fsclient.read_json_file(os.path.join(model_path, "options.json"))

        y_test, _ = ModelHelper.preprocess_target(model_path,
            records=[[100], [0], [34], [88], [44], [1]],
            features=["cnt"]
        )
        y_pred, _ = ModelHelper.preprocess_target(model_path,
            records=[[100], [0], [34], [88], [44], [1]],
            features=["cnt"]
        )

        scores = ModelHelper.calculate_scores(options, y_test=y_test, y_pred=y_pred)
        assert scores['mae_over'] == 0.0
        assert scores['mae_under'] == 0.0

        y_test, _ = ModelHelper.preprocess_target(model_path,
            records=[[100], [10], [34], [88], [44], [1]],
            features=["cnt"]
        )
        y_pred, _ = ModelHelper.preprocess_target(model_path,
            records=[[0], [0], [0], [0], [0], [0]],
            features=["cnt"]
        )

        scores = ModelHelper.calculate_scores(options, y_test=y_test, y_pred=y_pred)
        assert scores['mae_over'] == 0.0
        assert scores['mae_under'] >= 46.0

    def test_process_prediction(self):
        model_path = 'tests/fixtures/test_predict_by_model/iris'
        options = fsclient.read_json_file(os.path.join(model_path, "options.json"))
        target_categories = ["setosa", "versicolor", "virginica"]

        ds = DataFrame.create_dataframe(os.path.join(model_path, "iris_test.csv"))
        ds.drop([options['targetFeature']])
        results = ["setosa", "versicolor", "virginica", "setosa", "versicolor", "virginica"]
        results_proba =  None
        proba_classes = None

        ModelHelper.process_prediction(ds,
            results, results_proba, proba_classes,
            None, options.get('minority_target_class'),
            options['targetFeature'], target_categories)

        ds_test = DataFrame.create_dataframe(os.path.join(model_path, "iris_test.csv"))
        self.assertEqual(ds.dtypes, ds_test.dtypes)
        self.assertEqual(ds.df.values.tolist(), ds_test.df.values.tolist())

    def test_save_prediction(self):
        model_path = 'tests/fixtures/test_predict_by_model/iris'
        options = fsclient.read_json_file(os.path.join(model_path, "options.json"))

        prediction_id = "123"
        prediction_date="today"
        predicted_file_path = os.path.join(model_path, "predictions",
            "iris_test_"+prediction_id+"_"+options.get('uid')+"_predicted.csv")

        ds = DataFrame.create_dataframe(os.path.join(model_path, "iris_test.csv"))
        fsclient.remove_file(predicted_file_path)
        self.assertFalse(fsclient.is_file_exists(predicted_file_path))

        res = ModelHelper.save_prediction(ds, prediction_id,
            json_result=False, count_in_result=False, prediction_date=prediction_date,
            model_path=model_path, model_id=options.get('uid'))
        self.assertEqual(res, predicted_file_path)
        self.assertTrue(fsclient.is_file_exists(predicted_file_path))

        ds = DataFrame.create_dataframe(os.path.join(model_path, "iris_test.csv"))
        fsclient.remove_file(predicted_file_path)
        self.assertFalse(fsclient.is_file_exists(predicted_file_path))

        res = ModelHelper.save_prediction(ds, prediction_id,
            json_result=True, count_in_result=False, prediction_date=prediction_date,
            model_path=model_path, model_id=options.get('uid'))
        self.assertEqual( res['columns'], ds.columns)
        self.assertEqual( len(res['data']), 6)

        ds = DataFrame.create_dataframe(os.path.join(model_path, "iris_test.csv"))
        fsclient.remove_file(predicted_file_path)
        self.assertFalse(fsclient.is_file_exists(predicted_file_path))

        ds.options['data_path'] = None
        res = ModelHelper.save_prediction(ds, prediction_id,
            json_result=False, count_in_result=False, prediction_date=prediction_date,
            model_path=model_path, model_id=options.get('uid'))
        self.assertEqual( type(res[0]), dict)
        self.assertEqual( res[0][options['targetFeature']], 'setosa')

        ds = DataFrame.create_dataframe(os.path.join(model_path, "iris_test.csv"))
        fsclient.remove_file(predicted_file_path)
        self.assertFalse(fsclient.is_file_exists(predicted_file_path))

        ds.options['data_path'] = None
        ds.loaded_columns = ds.columns
        res = ModelHelper.save_prediction(ds, prediction_id,
            json_result=False, count_in_result=False, prediction_date=prediction_date,
            model_path=model_path, model_id=options.get('uid'))
        self.assertEqual( res['columns'], ds.columns)
        self.assertEqual( len(res['data']), 6)
        self.assertEqual( type(res['data'][0]), list)

    def test_process_prediction_proba(self):
        model_path = 'tests/fixtures/test_predict_by_model/iris'
        options = fsclient.read_json_file(os.path.join(model_path, "options.json"))
        target_categories = ["setosa", "versicolor", "virginica"]

        ds = DataFrame.create_dataframe(os.path.join(model_path, "iris_test.csv"))
        ds.drop([options['targetFeature']])
        results = None #[0, 1, 2, 0, 1, 2]
        results_proba =  [
            [0.8, 0.1, 0.1], [0.4, 0.6, 0.1], [0.1, 0.2, 0.7],
            [0.7, 0.2, 0.1], [0.3, 0.7, 0.1], [0.1, 0.3, 0.6]]
        results_proba = np.array(results_proba)
        proba_classes = [0, 1, 2]

        ModelHelper.process_prediction(ds,
            results, results_proba, proba_classes,
            0.5, None,
            options['targetFeature'], target_categories)

        ds_test = DataFrame.create_dataframe(os.path.join(model_path, "iris_test.csv"))
        self.assertEqual(ds.columns, ds_test.columns + ["proba_setosa","proba_versicolor","proba_virginica"])
        self.assertEqual(ds.df[options['targetFeature']].values.tolist(), ds_test.df[options['targetFeature']].values.tolist())

    def test_calculate_proba_target(self):
        res = ModelHelper.calculate_proba_target(
            [[0.2, 0.8], [0.9, 0.1]], [0,1], ["f", "t"], 0.5)
        self.assertEqual(res, [1, 0])

        res = ModelHelper.calculate_proba_target(
            [[0.2, 0.8], [0.9, 0.1]], [0,1], ["f", "t"], 0.9)
        self.assertEqual(res, [0, 0])

        res = ModelHelper.calculate_proba_target(
            [[0.2, 0.8], [0.6, 0.4]], [0,1], ["f", "t"], 0.7)
        self.assertEqual(res, [1, 0])

        res = ModelHelper.calculate_proba_target(
            [[0.2, 0.8], [0.6, 0.4]], [0,1], ["f", "t"], 0.4)
        self.assertEqual(res, [1, 1])

        res = ModelHelper.calculate_proba_target(
            [[0.2, 0.8], [0.6, 0.4]], [0,1], ["f", "t"], "0.4")
        self.assertEqual(res, [1, 1])

        res = ModelHelper.calculate_proba_target(
            [[0.2, 0.8], [0.6, 0.4]], [0,1], ["f", "t"], {"t": 0.7})
        self.assertEqual(res, [1, 0])

        res = ModelHelper.calculate_proba_target(
            [[0.2, 0.8], [0.6, 0.4]], [0,1], ["f", "t"], 0.7, minority_target_class="t")
        self.assertEqual(res, [1, 0])

        res = ModelHelper.calculate_proba_target(
            [[0.2, 0.8], [0.6, 0.4]], [0,1], ["f", "t"], {"t": 0.4})
        self.assertEqual(res, [1, 1])

        res = ModelHelper.calculate_proba_target(
            [[0.2, 0.8], [0.6, 0.4]], [0,1], ["f", "t"], "{\"t\": 0.4}")
        self.assertEqual(res, [1, 1])

        res = ModelHelper.calculate_proba_target(
            [[0.2, 0.3, 0.5], [0.6, 0.1, 0.3]], [0,1,2], ["f", "t", "u"], 0.4)
        self.assertEqual(res, [2, 0])

        res = ModelHelper.calculate_proba_target(
            [[0.2, 0.2, 0.6], [0.6, 0.1, 0.3]], [0,1,2], ["f", "t", "u"], {"u": 0.6})
        self.assertEqual(res, [2, 0])

        res = ModelHelper.calculate_proba_target(
            [[0.2, 0.2, 0.6], [0.6, 0.1, 0.3]], [0,1,2], ["f", "t", "u"], 0.6, minority_target_class="u")
        self.assertEqual(res, [2, 0])

        res = ModelHelper.calculate_proba_target(
            [[0.2, 0.2, 0.6], [0.1, 0.6, 0.3]], [0,1,2], ["f", "t", "u"], {"t": 0.6})
        self.assertEqual(res, [2, 1])

        res = ModelHelper.calculate_proba_target(
            [[0.9957942056, 0.0042057944]], [0,1], [" <=50K", " >50K"], 0.000001, minority_target_class=" >50K")
        self.assertEqual(res, [1])

    def test_create_model_options_file(self):
        res = ModelHelper.create_model_options_file(
            options_path='tests/temp/options.json',
            scoring='accuracy',
            target_column='test',
            task_type='classification',
            binary_classification=True,
        )

        self.assertEqual(res, {'targetFeature': 'test', 'task_type': 'classification', 'scoring': 'accuracy', 'score_name': 'accuracy', 'classification': True, 'binaryClassification': True, 'external_model': True, 'scoreNames': ['accuracy', 'average_precision', 'neg_log_loss', 'roc_auc', 'gini', 'f1', 'precision', 'recall', 'f1_micro', 'f1_macro', 'f1_weighted', 'precision_micro', 'precision_macro', 'precision_weighted', 'recall_micro', 'recall_macro', 'recall_weighted', 'cohen_kappa_score', 'matthews_corrcoef']})
