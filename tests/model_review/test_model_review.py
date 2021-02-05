import datetime
import dateutil
import glob
import json
import numpy
import os
import pandas as pd
import pathlib
import pytest
import re
import shutil
import time
import uuid

from pyarrow import feather

from a2ml.api.utils import fsclient
from a2ml.api.utils.dataframe import DataFrame
from a2ml.api.model_review.model_review import ModelReview
from tests.vcr_helper import vcr

def test_score_model_performance_daily():
    model_path = 'tests/fixtures/test_score_model_performance_daily/iris'
    date_from = datetime.date(2020, 10, 22)
    date_to = datetime.date(2020, 10, 22)

    res = ModelReview({'model_path': model_path}).score_model_performance_daily(str(date_from), date_to)

    assert type(res) is dict
    date_item = res[str(date_from)]
    assert type(date_item) is dict
    assert date_item['scores']
    assert date_item['score_name']
    score = date_item['scores'][date_item['score_name']]
    assert type(score) is numpy.float64
    assert score > 0
    assert 'review_metric' in date_item

def test_score_model_performance_daily():
    model_path = 'tests/fixtures/test_score_model_performance_daily/iris'
    date_from = datetime.date(2020, 10, 22)
    date_to = datetime.date(2020, 10, 22)

    res = ModelReview({'model_path': model_path}).score_model_performance_daily(str(date_from), date_to)

    assert type(res) is dict
    date_item = res[str(date_from)]
    assert type(date_item) is dict
    assert date_item['scores']
    assert date_item['score_name']
    score = date_item['scores'][date_item['score_name']]
    assert type(score) is numpy.float64
    assert score > 0
    assert 'review_metric' in date_item

def test_score_model_performance_daily_none_actuals():
    model_path = 'tests/fixtures/test_score_model_performance_daily/iris_no_matches'
    date_from = datetime.date(2020, 10, 21)
    date_to = datetime.date(2020, 10, 22)

    res = ModelReview({'model_path': model_path}).score_model_performance_daily(date_from, str(date_to))

    assert type(res) is dict
    date_item = res[str(date_from)]
    score = date_item['scores'][date_item['score_name']]
    assert score == 1 / 3
    date_item = res[str(date_to)]
    score = date_item['scores'][date_item['score_name']]
    assert score == 1 / 3

def test_score_model_performance_daily_fn_fp():
    # one of the files does not contain base line scores
    # then nan converted to category gives additional invalid class on confision matrix
    model_path = 'tests/fixtures/test_score_model_performance_daily/fp_fn_adult'
    date_from = datetime.date(2020, 12, 19)
    date_to = datetime.date(2020, 12, 19)

    res = ModelReview({'model_path': model_path}).score_model_performance_daily(date_from, str(date_to))

    assert type(res) is dict

    confusion_sum = lambda scores: scores['TN'] + scores['FP'] + scores['FN'] + scores['TP']
    date_res = res[str(date_to)]

    assert 2 == confusion_sum(date_res['scores'])
    assert 1 == confusion_sum(date_res['baseline_scores'])

    # actuals with base line result if FN
    assert date_res['baseline_scores']['FN'] == 1


def test_distribution_chart_stats_selfhosted_model():
    model_path = 'tests/fixtures/test_distribution_chart_stats/self_hosted'
    date_from = datetime.date(2020, 10, 22)
    date_to = datetime.date(2020, 10, 22)

    res = ModelReview(_load_metric_task_params(model_path)).distribution_chart_stats(date_from, date_to)

    assert type(res) is dict
    assert type(res[str(date_to)]) is dict

    assert res["base_stat"] == {'actual_species': {'dist': {'versicolor': 1, 'virginica': 1}, 'imp': 0}, 'predicted_species': {'dist': {'virginica': 2}, 'imp': 0}, 'sepal_length': {'avg': 4.0, 'std_dev': 1.4142135623730951, 'imp': 0}, 'sepal_width': {'avg': 3.0, 'std_dev': 1.4142135623730951, 'imp': 0}, 'petal_length': {'avg': 2.0, 'std_dev': 1.4142135623730951, 'imp': 0}, 'petal_width': {'avg': 1.0, 'std_dev': 0.0, 'imp': 0}}

    assert res[str(date_to)] == {
      "actual_species": {
        "dist": { "virginica": 2, "versicolor": 2 },
        "imp": 0
      },
      "predicted_species": {
        "dist": { "virginica": 4 },
        "imp": 0
      },
      "sepal_length": {
        "avg": 4.0,
        "std_dev": 1.4142135623730951,
        "imp": 0
      },
      "sepal_width": {
        "avg": 3.0,
        "std_dev": 1.4142135623730951,
        "imp": 0
      },
      "petal_length": {
        "avg": 2.0,
        "std_dev": 1.4142135623730951,
        "imp": 0
      },
      "petal_width": {
        "avg": 1.0,
        "std_dev": 0.0,
        "imp": 0
      }
    }

def test_distribution_chart_stats_for_categorical_target():
    model_path = 'tests/fixtures/test_distribution_chart_stats/iris'
    date_from = datetime.date(2020, 10, 22)
    date_to = datetime.date(2020, 10, 22)

    res = ModelReview(_load_metric_task_params(model_path)).distribution_chart_stats(date_from, date_to)
    assert type(res) is dict
    assert type(res[str(date_to)]) is dict

    assert res[str(date_to)] == {
      "actual_species": {
        "dist": { "virginica": 2, "versicolor": 2 },
        "imp": 0
      },
      "predicted_species": {
        "dist": { "virginica": 4 },
        "imp": 0
      },
      "sepal_length": {
        "avg": 4.0,
        "std_dev": 1.4142135623730951,
        "imp": 0
      },
      "sepal_width": {
        "avg": 3.0,
        "std_dev": 1.4142135623730951,
        "imp": 0
      },
      "petal_length": {
        "avg": 2.0,
        "std_dev": 1.4142135623730951,
        "imp": 0
      },
      "petal_width": {
        "avg": 1.0,
        "std_dev": 0.0,
        "imp": 0
      }
    }

def test_distribution_chart_stats_with_null_booleans():
    model_path = 'tests/fixtures/test_distribution_chart_stats/callouts'
    os.makedirs(os.path.join(model_path, 'predictions'), exist_ok=True)

    date_from = datetime.date(2020, 5, 7)
    date_to = datetime.date(2020, 5, 7)

    actuals = {
      'store_id': [40, 278],
      'company_id': [11, 37],
      'gender': [None, 'FEMALE'],
      'employee_age': [None, 24],
      'is_minor': [None, False],
      'marital_status': [None, 'SINGLE'],
      'race': [None, 'CAUCASIAN'],
      'shift_date': ['2020-05-09', '2020-05-17'],
      'is_weekend': [True, True],
      'start_time': ['2020-05-09T16:00:00+00:00', '2020-05-17T22:00:00+00:00'],
      'end_time': ['2020-05-09T19:15:00+00:00', '2020-05-18T06:00:00+00:00'],
      'unrecorded_no_show_count': [3, 0],
      'default_rate': [10, 12],
      'hire_date': [None, '2016-12-25'],
      'is_holiday': [False, False],
      'callin_cancel_count': [0, 0],
      'recently_cancel_count': [0, 0],
      'proba_False': [0.0216337, 0.999738],
      'proba_True': [0.978366, 0.000262292],
      'target': [True, True],
      'a2ml_predicted': [True, False],
    }

    remove_actual_files(model_path)
    write_actuals(model_path, actuals, with_features=True, date=date_from)

    res = ModelReview(_load_metric_task_params(model_path)).distribution_chart_stats(date_from, date_to)
    assert type(res) is dict
    assert type(res[str(date_to)]) is dict

    assert res[str(date_to)] == {
      'actual_target': {'avg': 1.0, 'std_dev': 0.0, 'imp': 0},
      'predicted_target': {'avg': 0.5, 'std_dev': 0.7071067811865476, 'imp': 0},
      'company_id': {'avg': 24.0, 'std_dev': 18.384776310850235, 'imp': 0},
      'gender': {'dist': {'FEMALE': 1}, 'imp': 0},
      'employee_age': {'avg': 24.0, 'imp': 0, 'std_dev': 0},
      'is_minor': {'dist': {False: 1}, 'imp': 0},
      'marital_status': {'dist': {'SINGLE': 1}, 'imp': 0},
      'race': {'dist': {'CAUCASIAN': 1}, 'imp': 0}, #0.041806
      'shift_date': {'dist': {'2020-05-17': 1, '2020-05-09': 1}, 'imp': 0},
      'is_weekend': {'avg': 1.0, 'std_dev': 0.0, 'imp': 0},
      'start_time': {'dist': {'2020-05-17T22:00:00+00:00': 1, '2020-05-09T16:00:00+00:00': 1}, 'imp': 0},
      'end_time': {'dist': {'2020-05-18T06:00:00+00:00': 1, '2020-05-09T19:15:00+00:00': 1}, 'imp': 0},
      'unrecorded_no_show_count': {'avg': 1.5, 'std_dev': 2.1213203435596424, 'imp': 0},
      'default_rate': {'avg': 11.0, 'std_dev': 1.4142135623730951, 'imp': 0},
      'hire_date': {'dist': {'2016-12-25': 1}, 'imp': 0},
      'is_holiday': {'avg': 0.0, 'std_dev': 0.0, 'imp': 0},
      'callin_cancel_count': {'avg': 0.0, 'std_dev': 0.0, 'imp': 0},
      'recently_cancel_count': {'dist': {0: 2}, 'imp': 0}
    }

def test_get_feature_importances_general_metrics_cache():
    model_path = 'tests/fixtures/test_distribution_chart_stats/adult'

    params = _load_metric_task_params(model_path)

    res = ModelReview(params).get_feature_importances()
    assert res == {'workclass': 0.12006373015194421, 'sex': 0.039481754114499897,
      'occupation': 0.20967661413259162, 'education': 0.2999579889231273,
      'relationship': 0.08698243068672135, 'marital-status': 0.14329620992107325,
      'race': 0.04180630794271793, 'native-country': 0.02072552576600564,
      'capital-loss': 0.2571256791934569, 'capital-gain': 0.31323744185565716,
      'hours-per-week': 0.4246393312722869, 'age': 0.7161049235052714, 'fnlwgt': 1.0}

def test_get_feature_importances_no_metrics_cache():
    model_path = 'tests/fixtures/test_distribution_chart_stats/adult'

    params = _load_metric_task_params(model_path)
    params['hub_info']['pipeline_id'] = '555555555555555'

    res = ModelReview(params).get_feature_importances()

    assert res == {}

def test_set_support_review_model_flag():
    # setup
    model_path = 'tests/fixtures/test_set_support_review_model_flag'
    shutil.copyfile(model_path + '/options_original.json', model_path + '/options.json')

    # test
    ModelReview({'model_path': model_path}).set_support_review_model_flag(True)

    res = {}

    with open(model_path + '/options.json', 'r') as f:
      res = json.load(f)

    assert res['support_review_model'] == True

    # teardown
    os.remove(model_path + '/options.json')

def test_remove_model():
    # arrange
    model_path = 'tests/fixtures/test_remove_model'
    fsclient.write_json_file(model_path + '/options.json', {})
    os.makedirs(model_path + '/predictions', exist_ok=True)
    pathlib.Path(model_path + '/predictions/somedata.csv').touch()
    assert os.path.exists(model_path) == True

    # act
    ModelReview({'model_path': model_path}).remove_model()

    # assert
    assert os.path.exists(model_path) == False

def test_clear_model_results_and_actuals():
    # arrange
    model_path = 'tests/fixtures/test_clear_model_results_and_actuals'
    fsclient.write_json_file(model_path + '/options.json', {})

    os.makedirs(model_path + '/predictions', exist_ok=True)
    pathlib.Path(model_path + '/predictions/somedata.csv').touch()
    assert os.path.exists(model_path) == True

    # act
    ModelReview({'model_path': model_path}).clear_model_results_and_actuals()

    # assert
    assert os.path.exists(model_path) == True
    assert os.path.exists(os.path.join(model_path, 'options.json')) == True
    assert os.path.exists(os.path.join(model_path, 'predictions')) == False

def test_score_actuals_should_not_convert_predicted_categorical_to_int_in_actuals_file():
    model_path = 'tests/fixtures/test_score_actuals/categorical_convert'

    remove_actual_files(model_path)

    actuals = [
      {
        'actual': 'good',
        'checking_status': 'no checking',
        'duration': 6,
        'credit_history': 'all paid',
        'purpose': 'radio/tv',
        'credit_amount': 1750,
        'savings_status': '500<=X<1000',
        'employment': '>=7',
        'installment_commitment': 2,
        'personal_status': 'male single',
        'other_parties': 'none',
        'residence_since': 4,
        'property_magnitude': 'life insurance',
        'age': 45,
        'other_payment_plans': 'bank',
        'housing': 'own',
        'existing_credits': 1,
        'job': 'unskilled resident',
        'num_dependents': 2,
        'own_telephone': 'none',
        'foreign_worker': 'yes',
        'class': 'good',
      }
    ]

    actual_date = datetime.date(2020, 8, 3)

    res = ModelReview({'model_path': model_path}).add_actuals(
      None, actuals_path=None, data=actuals, actual_date=str(actual_date), return_count=True
    )

    for (_date, _path, actuals) in assert_actual_file(model_path, actual_date=actual_date, with_features=True):
      assert actuals[0]['class'] == 'good'
      assert actuals[0]['a2ml_predicted'] == 'good'
      assert actuals[0]['checking_status'] == 'no checking'

def test_score_actuals_dict_full():
    model_path = 'tests/fixtures/test_score_actuals/iris'

    remove_actual_files(model_path)

    actuals = [
      {
        'species': 'virginica',
        'actual': 'versicolor',
        'sepal_length': 5.0,
        'sepal_width': 4.0,
        'petal_length': 3.0,
        'petal_width': 1.0,
        'baseline_target': 'virginica'
      },
      {
        'species': 'virginica',
        'actual': 'virginica',
        'sepal_length': 3.0,
        'sepal_width': 2.0,
        'petal_length': 1.0,
        'petal_width': 1.0,
        'baseline_target': 'virginica'
      },
    ]

    roi = {
        'filter': '$petal_width > 0 and $sepal_width > 1 and $sepal_length * $sepal_width >= 5',
        'revenue': '@if(A="virginica", $150, @if(A = "versicolor", $100, $0))',
        'investment': '$50',
    }

    res = ModelReview({'model_path': model_path, 'roi': roi}).add_actuals(
        None,
        actuals_path=None,
        data=actuals,
        return_count=True,
    )

    assert res['score']['accuracy'] == 0.5
    assert res['baseline_score']['accuracy'] == 0.5
    assert res['count'] == 2
    assert res['score']['roi'] == (250 - 100) / 100

    for (_date, _path, actuals) in assert_actual_file(model_path, with_features=True):
      assert actuals[0]['a2ml_predicted'] == 'virginica'
      assert actuals[0]['species'] == 'versicolor'
      assert actuals[0]['sepal_length'] == 5.0

      assert actuals[1]['a2ml_predicted'] == 'virginica'
      assert actuals[1]['species'] == 'virginica'
      assert actuals[1]['sepal_length'] == 3.0

    res2 = ModelReview({'model_path': model_path}).score_model_performance_daily(None, None)
    assert res2['today']['baseline_scores']['accuracy'] == 0.5

def test_score_actuals_dict_list_full():
    model_path = 'tests/fixtures/test_score_actuals/iris'

    remove_actual_files(model_path)

    actuals = {
      'species': ['virginica', 'virginica'],
      'actual': ['versicolor', 'virginica'],
      'sepal_length': [5.0, 3.0],
      'sepal_width': [4.0, 2.0],
      'petal_length': [3.0, 1.0],
      'petal_width': [1.0, 1.0],
    }

    res = ModelReview({'model_path': model_path}).add_actuals(None, actuals_path=None, data=actuals)

    assert res['accuracy'] == 0.5

    for (_date, _path, actuals) in assert_actual_file(model_path, with_features=True):
      assert actuals[0]['a2ml_predicted'] == 'virginica'
      assert actuals[0]['species'] == 'versicolor'
      assert actuals[0]['sepal_length'] == 5.0

      assert actuals[1]['a2ml_predicted'] == 'virginica'
      assert actuals[1]['species'] == 'virginica'
      assert actuals[1]['sepal_length'] == 3.0

@vcr.use_cassette('model_review/score_actuals_return_count/predict.yaml')
def test_score_actuals_dict_wo_predicted():
    model_path = 'tests/fixtures/test_score_actuals/iris'

    remove_actual_files(model_path)

    actuals = [
      {
        "actual": "setosa",
        "sepal_length": 5.1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2
      },
      {
        "actual": "setosa",
        "sepal_length": 5.2,
        "sepal_width": 3.6,
        "petal_length": 1.5,
        "petal_width": 0.3
      },
    ]

    params = _load_score_task_params(model_path)
    ctx = _build_context(params)

    res = ModelReview(params).add_actuals(
      ctx, actuals_path=None, data=actuals, return_count=True
    )

    assert res['count'] == 2
    assert res['score']['accuracy'] == 1.0

    for (_date, _path, actuals) in assert_actual_file(model_path, with_features=True):
      assert actuals[0]['a2ml_predicted'] == 'setosa'
      assert actuals[0]['species'] == 'setosa'
      assert actuals[0]['sepal_length'] == 5.1

      assert actuals[1]['a2ml_predicted'] == 'setosa'
      assert actuals[1]['species'] == 'setosa'
      assert actuals[1]['sepal_length'] == 5.2

def test_score_actuals_dict_wo_features():
    model_path = 'tests/fixtures/test_score_actuals/iris'

    remove_actual_files(model_path)

    actuals = [
      { 'species': 'virginica', 'actual': 'versicolor' },
      { 'species': 'virginica', 'actual': 'virginica' },
    ]

    res = ModelReview({'model_path': model_path}).add_actuals(None, actuals_path=None, data=actuals)

    assert res['accuracy'] == 0.5

    for (_date, _path, actuals) in assert_actual_file(model_path, with_features=False):
      assert actuals[0]['a2ml_predicted'] == 'virginica'
      assert actuals[0]['species'] == 'versicolor'

      assert actuals[1]['a2ml_predicted'] == 'virginica'
      assert actuals[1]['species'] == 'virginica'

def test_score_actuals_dict_wo_prediction_and_missing_features():
    model_path = 'tests/fixtures/test_score_actuals/iris'

    remove_actual_files(model_path)

    actuals = [{ 'actual': 'versicolor', 'sepal_length': 1.0, 'petal_length': 2.0 }]

    with pytest.raises(Exception, match=r"Missing features to make prediction: petal_width, sepal_width. Please, provide target 'species' or all training features to run predict."):
      ModelReview({'model_path': model_path}).add_actuals(None, data=actuals)

def test_score_actuals_dict_only_actual():
    model_path = 'tests/fixtures/test_score_actuals/iris'

    remove_actual_files(model_path)

    actuals = [{ 'actual': 'versicolor' }]

    with pytest.raises(
      Exception,
      match=r"Missing features to make prediction: petal_length, petal_width, sepal_length, sepal_width. Please, provide target 'species' or all training features to run predict."
    ):
      ModelReview({'model_path': model_path}).add_actuals(None, data=actuals)

def test_score_actuals_dict_only_prediction():
    model_path = 'tests/fixtures/test_score_actuals/iris'

    remove_actual_files(model_path)

    actuals = [{ 'species': 'versicolor' }]

    with pytest.raises(Exception, match=r"There is no 'actual' column in data"):
      ModelReview({'model_path': model_path}).add_actuals(None, data=actuals)

# We do not support it
# def test_score_actuals_dict_with_predicted_none():
#     model_path = 'tests/fixtures/test_score_actuals'

#     remove_actual_files(model_path)

#     row = {
#       'age': 33,
#       'capital-gain': 0,
#       'capital-loss': 0,
#       'education': 'Some-college',
#       'fnlwgt': 1,
#       'hours-per-week': 40,
#       'marital-status': 'Never-married',
#       'native-country': 'United-States',
#       'occupation': 'Prof-specialty',
#       'race': 'White',
#       'relationship': 'Not-in-family',
#       'sex': 'Male',
#       'workclass': 'Private'
#     }

#     actuals = [
#       {'feature1': 1, 'income': True, 'actual': None },
#       {'feature1': 1.1, 'income': False,'actual': None },
#       {'feature1': 1.3, 'income': False,'actual': None },
#     ]

#     for actual in actuals:
#       actual.update(row)

#     res = ModelReview({'model_path': model_path}).add_actuals(
#       None, actuals_path=None, data=actuals, return_count=True
#     )

#     assert res['count'] == 3
#     assert res['score']['accuracy'] == 0.0

#     for (_date, _path, actuals) in assert_actual_file(model_path, with_features=True):
#       assert actuals[0]['a2ml_predicted'] == True
#       assert actuals[0]['income'] == None
#       assert actuals[0]['age'] == 33

#       assert actuals[1]['a2ml_predicted'] == False
#       assert actuals[1]['income'] == None

#       assert actuals[2]['a2ml_predicted'] == False
#       assert actuals[2]['income'] == None

def test_score_iris_csv_full():
    model_path = 'tests/fixtures/test_score_actuals/lucas-iris'

    remove_actual_files(model_path)

    res = ModelReview({'model_path': model_path}).add_actuals(
      None, actuals_path='tests/fixtures/test_score_actuals/lucas-iris/iris_actuals.csv')

    assert res['accuracy'] == 1.0

    for (_date, _path, actuals) in assert_actual_file(model_path, with_features=True):
      assert actuals[0]['a2ml_predicted'] == 'Iris-setosa'
      assert actuals[0]['class'] == 'Iris-setosa'
      assert actuals[0]['sepal_length'] == 5.1

def test_score_iris_csv_full_with_date_columns():
    model_path = 'tests/fixtures/test_score_actuals/lucas-iris'
    actuals_path = os.path.join(model_path, 'iris_actuals_with_dates.csv')

    remove_actual_files(model_path)

    res = ModelReview({'model_path': model_path}).add_actuals(
      None,
      actuals_path=actuals_path,
      actual_date_column='date'
    )
    actuals = DataFrame.create_dataframe(data_path=actuals_path)

    assert res['accuracy'] == 1.0

    saved_actuals = list(assert_actual_file(model_path, with_features=True))

    assert len(saved_actuals) == 4

    ((day1, _, actuals1), (day2, _, actuals2), (day3, _, actuals3), (day4, _, actuals4)) = saved_actuals

    assert str(day1) == '2020-10-21' # date used
    assert str(day2) == '2020-10-22' # date used
    assert str(day3) == '2020-10-23' # time is covreted to date
    assert str(day4) == str(datetime.date.today()) # today is used for rows without date

    assert len(actuals1) + len(actuals2) + len(actuals3) + len(actuals4) == len(actuals)


@vcr.use_cassette('model_review/score_actuals_no_target/predict.yaml')
def test_score_iris_csv_wo_predicted():
    model_path = 'tests/fixtures/test_score_actuals/lucas-iris'

    remove_actual_files(model_path)

    params = _load_score_task_params(model_path)
    ctx = _build_context(params)

    res = ModelReview(params).add_actuals(
      ctx, actuals_path='tests/fixtures/test_score_actuals/lucas-iris/iris_actuals_wo_predictions.csv',
    )

    assert res['accuracy'] == 1.0

    for (_date, _path, actuals) in assert_actual_file(model_path, with_features=True):
      assert actuals[0]['a2ml_predicted'] == 'setosa'
      assert actuals[0]['class'] == 'setosa'
      assert actuals[0]['sepal_length'] == 5.1

def test_score_iris_csv_wo_features():
    model_path = 'tests/fixtures/test_score_actuals/lucas-iris'

    remove_actual_files(model_path)

    res = ModelReview({'model_path': model_path}).add_actuals(
      None, actuals_path='tests/fixtures/test_score_actuals/lucas-iris/iris_actuals_wo_features.csv')

    assert res['accuracy'] == 1.0

    for (_date, _path, actuals) in assert_actual_file(model_path, with_features=False):
      assert actuals[0]['a2ml_predicted'] == 'Iris-setosa'
      assert actuals[0]['class'] == 'Iris-setosa'

def test_score_actuals_lucas_case_array_full():
    model_path = 'tests/fixtures/test_score_actuals/lucas-iris'

    remove_actual_files(model_path)

    actuals = [
      ["Iris-setosa", 5.1, 3.5, 1.4, 0.2, "Iris-setosa"],
      ["Iris-setosa", 4.9, 3.0, 1.4, 0.2, "Iris-setosa"],
      ["Iris-setosa", 4.7, 3.2, 1.3, 0.2, "Iris-setosa"],
      ["Iris-setosa", 4.6, 3.1, 1.5, 0.2, "Iris-setosa"],
      ["Iris-setosa", 5.0, 3.6, 1.4, 0.2, "Iris-setosa"],
      ["Iris-setosa", 5.4, 3.9, 1.7, 0.4, "Iris-setosa"],
      ["Iris-setosa", 4.6, 3.4, 1.4, 0.3, "Iris-setosa"],
      ["Iris-setosa", 5.0, 3.4, 1.5, 0.2, "Iris-setosa"],
      ["Iris-setosa", 4.4, 2.9, 1.4, 0.2, "Iris-setosa"],
    ]

    actual_columns = ["actual", "sepal_length", "sepal_width", "petal_length", "petal_width", "class"]

    res = ModelReview({'model_path': model_path}).add_actuals(
      None, data=actuals, columns=actual_columns
    )

    assert res['accuracy'] == 1.0

    for (_date, _path, actuals) in assert_actual_file(model_path, with_features=True):
      assert actuals[0]['a2ml_predicted'] == 'Iris-setosa'
      assert actuals[0]['class'] == 'Iris-setosa'
      assert actuals[0]['sepal_length'] == 5.1

@vcr.use_cassette('model_review/score_actuals_no_target/predict.yaml')
def test_score_actuals_lucas_case_array_wo_prediceted():
    model_path = 'tests/fixtures/test_score_actuals/lucas-iris'

    remove_actual_files(model_path)

    actuals = [
      # actual sepal_length sepal_width petal_length petal_width
      [5.1, 3.5, 1.4, 0.2, "setosa"],
    ]

    actual_columns = ["sepal_length", "sepal_width", "petal_length", "petal_width", "actual"]

    params = _load_score_task_params(model_path)
    ctx = _build_context(params)
    res = ModelReview(params).add_actuals(ctx, data=actuals, columns=actual_columns)

    assert res['accuracy'] == 1.0

    for (_date, _path, actuals) in assert_actual_file(model_path, with_features=True):
      assert actuals[0]['a2ml_predicted'] == 'setosa'
      assert actuals[0]['class'] == 'setosa'
      assert actuals[0]['sepal_length'] == 5.1

def test_score_actuals_lucas_case_array_wo_features():
    model_path = 'tests/fixtures/test_score_actuals/lucas-iris'

    remove_actual_files(model_path)

    actuals = [
      ["Iris-setosa", "Iris-setosa"],
      ["Iris-setosa", "Iris-setosa"],
      ["Iris-setosa", "Iris-virginica"],
    ]

    actual_columns = ["actual", "class"]

    res = ModelReview({'model_path': model_path}).add_actuals(
      None, data=actuals, columns=actual_columns
    )

    assert res['accuracy'] == 2 / 3

    for (_date, _path, actuals) in assert_actual_file(model_path, with_features=False):
      assert actuals[0]['a2ml_predicted'] == 'Iris-setosa'
      assert actuals[0]['class'] == 'Iris-setosa'

      assert actuals[2]['a2ml_predicted'] == 'Iris-virginica'
      assert actuals[2]['class'] == 'Iris-setosa'

def test_score_actuals_another_result_first():
  model_path = 'tests/fixtures/test_score_actuals/another_result_first'

  remove_actual_files(model_path)

  actuals = [
    {
      'actual':'good',
      'class': 'good',
      'checking_status': "'0<=X<200'",
      'duration': 9,
      'credit_history': "'existing paid'",
      'purpose': "radio/tv",
      'credit_amount': 790,
      'savings_status': "'500<=X<1000'",
      'employment': "'1<=X<4'",
      'installment_commitment': 4,
      'personal_status': "'female div/dep/mar'",
      'other_parties': " none",
      'residence_since': 3,
      'property_magnitude': "'real estate'",
      'age': 66,
      'other_payment_plans': "none",
      'housing': "own",
      'existing_credits': 1,
      'job': "'unskilled resident'",
      'num_dependents': 1,
      'own_telephone': "none",
      'foreign_worker': "yes",
    },
  ]

  roi = {
    'filter': 'P="good"',
    'revenue': '@if(A="good", $1050, $0)',
    'investment': '$1000',
  }

  res = ModelReview({'model_path': model_path, 'roi': roi}).add_actuals(None, data=actuals)
  assert res['accuracy'] == 1
  assert res['roi'] == (1050 - 1000) / 1000

def test_build_review_data():
    model_path = "tests/fixtures/test_build_review_data/iris"
    data_path = "tests/fixtures/test_build_review_data/iris_class_review_B6FD93C248984BC_review_8E0B1F1D71A44DF.csv"
    full_actuals_path = "predictions/2020-10-22_F856362B6833492_full_data.feather.zstd"

    res = ModelReview({'model_path': model_path}).build_review_data(data_path=data_path)

    assert re.match(".*/iris_class_review_[0-9A-F]{15}.parquet", res)
    assert 'B6FD93C248984BC' not in res

    source_df = DataFrame({}).load_from_file(data_path)
    actuals_df = DataFrame({}).load_from_file(os.path.join(model_path, full_actuals_path))
    review_df = DataFrame({}).load_from_file(res)

    assert len(review_df) == len(source_df) + len(actuals_df)# - 1
    # We do not drop duplicates, since it is incorrect behaviour
    # Should drop one duplicated row  `5.1,3.5,1.4,0.2,Iris-setosa`

    for review_data_path in glob.glob('tests/fixtures/test_build_review_data/iris_class_review_*.parquet'):
      os.remove(review_data_path)

# def test_build_review_data_2():
#     model_path = 'tests/fixtures/test_distribution_chart_stats/bikesharing'

#     res = ModelReview({'model_path': model_path}).build_review_data(
#       data_path="tests/fixtures/bike_sharing_small.csv", date_col='dteday')
#     assert res
#     assert res.endswith(".parquet")

@pytest.mark.parametrize(
  "with_predictions, begin_date, end_date, expected_files_left",
  [
    pytest.param(True, None, None, [], id='Delete everything in whole range'),
    pytest.param(
      True,
      '2020-02-20',
      '2020-08-02',
      [
        '2020-10-22_638A9CF95B254D0_no_features_data.feather.zstd',
        '2020-10-22_F281E06F0CB44CB_full_data.feather.zstd'
      ], id='Delete everything in some range'
    ),
    pytest.param(
      False,
      None,
      None,
      ['2020-08-02_d8f4a1d6-43c4-41bb-b1d3-4926faaad975_results.feather.zstd'],
      id='Delete actuals in whole range'
    ),
  ]
)
def test_delete_actuals(with_predictions, begin_date, end_date, expected_files_left):
    # arrange
    model_path = 'tests/fixtures/test_delete_actuals'
    predictions_path = model_path + '/predictions/'
    fsclient.write_json_file(model_path + '/options.json', {})
    os.makedirs(predictions_path, exist_ok=True)
    pathlib.Path(predictions_path + '2020-02-20_549AA373A8FB470_actuals.feather.zstd').touch()
    pathlib.Path(predictions_path + '2020-08-02_d8f4a1d6-43c4-41bb-b1d3-4926faaad975_results.feather.zstd').touch()
    pathlib.Path(predictions_path + '2020-10-22_638A9CF95B254D0_no_features_data.feather.zstd').touch()
    pathlib.Path(predictions_path + '2020-10-22_F281E06F0CB44CB_full_data.feather.zstd').touch()
    assert os.path.exists(model_path) == True

    # act
    ModelReview({'model_path': model_path}).delete_actuals(
      with_predictions=with_predictions,
      begin_date=begin_date,
      end_date=end_date,
    )

    # assert
    files_left = os.listdir(predictions_path) if os.path.exists(predictions_path) else []
    assert sorted(files_left) == sorted(expected_files_left)

def test_validate_roi_syntax():
    expressions = [
        "(1 + A) * $100",
        "somefunc(1)",
        "$sepal_length + $sepal_width + $petal_length + $petal_width + $species + A + P",
        "$some_feature + A",
        "",
    ]

    model_path = 'tests/fixtures/test_validate_roi_syntax'
    res = ModelReview({'model_path': model_path}).validate_roi_syntax(expressions)

    assert len(res) == 5

    assert res[0]["expression"] == expressions[0]
    assert res[0]["is_valid"] == True, res[0]["error"]
    assert res[0]["error"] == None

    assert res[1]["expression"] == expressions[1]
    assert res[1]["is_valid"] == False, res[1]["error"]
    assert res[1]["error"] == "unknown function 'somefunc' at position 1"

    assert res[2]["expression"] == expressions[2]
    assert res[2]["is_valid"] == True, res[2]["error"]
    assert res[2]["error"] == None

    assert res[3]["expression"] == expressions[3]
    assert res[3]["is_valid"] == False, res[3]["error"]
    assert res[3]["error"] == "unknown variable '$some_feature' at position 1"

    assert res[4]["expression"] == expressions[4]
    assert res[4]["is_valid"] == True, res[4]["error"]
    assert res[4]["error"] == None

def write_actuals(model_path, actuals, with_features=True, date=None):
    df = pd.DataFrame(data=actuals)
    date = str(date or datetime.date.today())
    uid = uuid.uuid4().hex[:15].upper()
    suffix = "full_data" if with_features else "no_features_data"
    feather.write_feather(
      df,
      os.path.join(model_path, "predictions", date + "_" + uid + "_" + suffix + ".feather.zstd"),
      compression="zstd"
    )

def remove_actual_files(model_path):
    os.makedirs(os.path.join(model_path, 'predictions'), exist_ok=True)

    for actuals_path in glob.glob(model_path + '/predictions/*_data.feather.zstd'):
      os.remove(actuals_path)

def assert_actual_file(model_path, actual_date=None, with_features=True):
    actual_files = glob.glob(model_path + '/predictions/*_data.feather.zstd')
    actual_files.sort()

    assert len(actual_files) > 0

    for actual_file in actual_files:
      if actual_date:
        assert str(actual_date) in actual_file

      if with_features:
        assert actual_file.endswith("_full_data.feather.zstd")
      else:
        assert actual_file.endswith("_no_features_data.feather.zstd")

      stored_actuals = DataFrame({})
      stored_actuals.loadFromFeatherFile(actual_file)
      stored_actuals = json.loads(stored_actuals.df.to_json(orient='records'))

      if with_features:
        assert len(stored_actuals[0]) > 2
      else:
        assert len(stored_actuals[0]) == 2

      date = dateutil.parser.parse(os.path.basename(actual_file).split("_")[0]).date()

      yield(date, actual_file, stored_actuals)

def _build_context(params):
    from a2ml.tasks_queue.tasks_hub_api import _create_provider_context, _read_hub_experiment_session

    ctx = _create_provider_context(params)
    ctx = _read_hub_experiment_session(ctx, params)
    ctx.config.clean_changes()

    ctx.credentials = {
      'api_url': 'https://app-staging.auger.ai',
      'token': 'secret',
      'organization': 'mt-org',
    }

    return ctx

def _load_metric_task_params(model_path):
    path = 'tests/fixtures/test_distribution_chart_stats/metric_task_params.json'

    res = {}

    with open(path, 'r') as f:
      res = json.load(f)

    res['model_path'] = model_path
    res['metrics_rebuild'] = False
    res['hub_info']['experiment_id'] = 'b04782c60b1bc194'
    res['hub_info']['experiment_session_id'] = '2cf2db7ae6eca1e0'
    res['hub_info']['project_path'] = 'tests/fixtures/test_distribution_chart_stats'

    return res

def _load_score_task_params(model_path):
    path = model_path + '/score_task_params.json'

    res = {}

    with open(path, 'r') as f:
      res = json.load(f)

    res['model_path'] = model_path
    res['hub_info']['project_path'] = model_path

    return res
