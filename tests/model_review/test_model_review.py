import datetime
import glob
import json
import numpy
import os
import pathlib
import shutil
import time

from a2ml.api.utils import fsclient
from a2ml.api.utils.dataframe import DataFrame
from a2ml.api.model_review.model_review import ModelReview
from a2ml.tasks_queue.tasks_hub_api import _create_provider_context, _read_hub_experiment_session
from tests.vcr_helper import vcr

def test_score_model_performance_daily():
    model_path = 'tests/fixtures/test_score_model_performance_daily/iris'
    date_from = datetime.date(2020, 2, 16)
    date_to = datetime.date(2020, 2, 18)

    res = ModelReview({'model_path': model_path}).score_model_performance_daily(str(date_from), date_to)
    assert type(res) is dict
    assert type(res[str(date_from)]) is numpy.float64
    assert res[str(date_from)] > 0

def test_score_model_performance_daily_none_actuals():
    model_path = 'tests/fixtures/test_score_model_performance_daily/iris_no_matches'
    date_from = datetime.date(2020, 2, 16)
    date_to = datetime.date(2020, 2, 18)

    res = ModelReview({'model_path': model_path}).score_model_performance_daily(date_from, str(date_to))
    assert type(res) is dict
    assert res[str(date_from)] == 0.2

# def test_score_model_performance_daily_not_full_actuals():
#     model_path = 'tests/fixtures/test_score_model_performance_daily/iris_not_full_actuals'
#     date_from = datetime.date(2020, 3, 12)
#     date_to = datetime.date(2020, 3, 13)

#     res = ModelReview({'model_path': model_path}).score_model_performance_daily(date_from, str(date_to))
#     assert type(res) is dict
#     assert res[str(date_to)] == 0

def test_distribution_chart_stats():
    model_path = 'tests/fixtures/test_distribution_chart_stats/bikesharing'
    date_from = datetime.date(2020, 2, 16)
    date_to = datetime.date(2020, 2, 19)

    res = ModelReview(_load_metric_task_params(model_path)).distribution_chart_stats(date_from, date_to)
    assert type(res) is dict
    assert type(res[str(date_to)]) is dict

    assert res[str(date_to)] == {
      'predicted_cnt': { 'avg': 483.18357849636016, 'std_dev': 0.0, 'imp': 0 },
      'dteday': { 'avg': 0.0,  'std_dev': 0.0, 'imp': 0 },
      'season': { 'dist': { 0: 2 }, 'imp': 0},
      'yr': { 'dist': { 0: 2 }, 'imp': 0 },
      'mnth': { 'avg': 0.0, 'std_dev': 0.0, 'imp': 0 },
      'holiday': { 'dist': { 0: 2 }, 'imp': 0},
      'weekday': { 'dist': { 0: 2 }, 'imp': 0},
      'workingday': { 'dist': { 0: 2 }, 'imp': 0},
      'weathersit': { 'dist': { 0: 2 }, 'imp': 0},
      'temp': { 'avg': 0.0, 'std_dev': 0.0, 'imp': 0 },
      'atemp': { 'avg': 0.0, 'std_dev': 0.0, 'imp': 0 },
      'hum': { 'avg': 0.0, 'std_dev': 0.0, 'imp': 0 },
      'casual': { 'avg': 0.0, 'std_dev': 0.0, 'imp': 0 },
      'registered': { 'avg': 0.0, 'std_dev': 0.0, 'imp': 0 },
      'actual_cnt': { 'avg': 2.6, 'std_dev': 2.073644135332772, 'imp': 0 },
    }

def test_distribution_chart_stats_for_categorical_target():
    model_path = 'tests/fixtures/test_distribution_chart_stats/adult'
    date_from = datetime.date(2020, 2, 16)
    date_to = datetime.date(2020, 2, 20)

    res = ModelReview(_load_metric_task_params(model_path)).distribution_chart_stats(date_from, date_to)
    assert type(res) is dict
    assert type(res[str(date_to)]) is dict

    assert res[str(date_to)] == {
      'predicted_income': {'dist': {' <=50K': 1}, 'imp': 0},
      'age': {'avg': 0.0, 'std_dev': 0, 'imp': 0.716105},
      'workclass': {'dist': {0: 1}, 'imp': 0.120064},
      'fnlwgt': {'avg': 0.0, 'std_dev': 0, 'imp': 1.0},
      'education': {'dist': {0: 1}, 'imp': 0.299958},
      'education-num': {'avg': 0.0, 'std_dev': 0, 'imp': 0},
      'marital-status': {'dist': {0: 1}, 'imp': 0.143296},
      'occupation': {'dist': {0: 1}, 'imp': 0.209677},
      'relationship': {'dist': {0: 1}, 'imp': 0.086982},
      'race': {'dist': {0: 1}, 'imp': 0.041806},
      'sex': {'dist': {0: 1}, 'imp': 0.039482},
      'capital-gain': {'avg': 0.0, 'std_dev': 0, 'imp': 0.313237},
      'capital-loss': {'avg': 0.0, 'std_dev': 0, 'imp': 0.257126},
      'hours-per-week': {'avg': 0.0, 'std_dev': 0, 'imp': 0.424639},
      'native-country': {'dist': {0: 1}, 'imp': 0.020726},
      'actual_income': {'dist': {' <=50K': 1}, 'imp': 0},
    }

def test_distribution_chart_stats_with_null_booleans():
    model_path = 'tests/fixtures/test_distribution_chart_stats/callouts'
    date_from = datetime.date(2020, 5, 7)
    date_to = datetime.date(2020, 5, 7)

    res = ModelReview(_load_metric_task_params(model_path)).distribution_chart_stats(date_from, date_to)
    assert type(res) is dict
    assert type(res[str(date_to)]) is dict

    assert res[str(date_to)] == {
      'predicted_target': {'avg': 0.5, 'std_dev': 0.7071067811865476, 'imp': 0},
      'company_id': {'avg': 24.0, 'std_dev': 18.384776310850235, 'imp': 0},
      'gender': {'dist': {'FEMALE': 1}, 'imp': 0},
      'employee_age': {'dist': {}, 'imp': 0},
      'is_minor': {'dist': {}, 'imp': 0},
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
    # os.makedirs(model_path, exist_ok=True)
    # pathlib.Path(model_path + '/options.json').touch()
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

    # os.makedirs(model_path, exist_ok=True)
    # pathlib.Path(model_path + '/options.json').touch()
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

    for actuals_path in glob.glob(model_path + '/predictions/*_actuals.feather.zstd'):
      os.remove(actuals_path)

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
      None, actuals_path=None, actual_records=actuals, actual_date=str(actual_date), return_count=True
    )

    actual_files = glob.glob(model_path + '/predictions/*_actuals.feather.zstd')
    assert len(actual_files) > 0
    assert str(actual_date) in actual_files[0]

    stored_actuals = DataFrame({})
    stored_actuals.loadFromFeatherFile(actual_files[0])

    stored_actuals = json.loads(stored_actuals.df.to_json(orient='records'))

    assert stored_actuals[0]['class'] == 'good'
    assert stored_actuals[0]['a2ml_predicted'] == 'good'

def test_score_actuals_dict_full():
    model_path = 'tests/fixtures/test_score_actuals/iris'

    for actuals_path in glob.glob(model_path + '/predictions/*_actuals.feather.zstd'):
      os.remove(actuals_path)

    actuals = [
      {
        'species': 'virginica',
        'actual': 'versicolor',
        'sepal_length': 5.0,
        'sepal_width': 4.0,
        'petal_length': 3.0,
        'petal_width': 1.0,
      },
      {
        'species': 'virginica',
        'actual': 'virginica',
        'sepal_length': 3.0,
        'sepal_width': 2.0,
        'petal_length': 1.0,
        'petal_width': 1.0,
      },
    ]

    res = ModelReview({'model_path': model_path}).add_actuals(None, actuals_path=None, actual_records=actuals)

    assert res['accuracy'] == 0.5

@vcr.use_cassette('model_review/score_actuals_return_count/predict.yaml')
def test_score_actuals_dict_wo_predicted():
    model_path = 'tests/fixtures/test_score_actuals/iris'

    for actuals_path in glob.glob(model_path + '/predictions/*_actuals.feather.zstd'):
      os.remove(actuals_path)

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
      ctx, actuals_path=None, actual_records=actuals, return_count=True
    )

    assert res['count'] == 2
    assert res['score']['accuracy'] == 1.0

def test_score_actuals_dict_wo_features():
    model_path = 'tests/fixtures/test_score_actuals/iris'

    for actuals_path in glob.glob(model_path + '/predictions/*_actuals.feather.zstd'):
      os.remove(actuals_path)

    actuals = [
      { 'species':'virginica', 'actual':'versicolor' },
      { 'species':'virginica', 'actual':'virginica' },
    ]

    res = ModelReview({'model_path': model_path}).add_actuals(None, actuals_path=None, actual_records=actuals)

    assert res['accuracy'] == 0.5

def test_score_actuals_dict_with_predicted_none():
    model_path = 'tests/fixtures/test_score_actuals'

    for actuals_path in glob.glob(model_path + '/predictions/*_actuals.feather.zstd'):
      os.remove(actuals_path)

    row = {
      'age': 33,
      'capital-gain': 0,
      'capital-loss': 0,
      'education': 'Some-college',
      'fnlwgt': 1,
      'hours-per-week': 40,
      'marital-status': 'Never-married',
      'native-country': 'United-States',
      'occupation': 'Prof-specialty',
      'race': 'White',
      'relationship': 'Not-in-family',
      'sex': 'Male',
      'workclass': 'Private'
    }

    actuals = [
      {'feature1': 1, 'income': True, 'actual': None },
      {'feature1': 1.1, 'income': False,'actual': None },
      {'feature1': 1.3, 'income': False,'actual': None },
    ]

    for actual in actuals:
      actual.update(row)

    res = ModelReview({'model_path': model_path}).add_actuals(
      None, actuals_path=None, actual_records=actuals, return_count=True
    )

    assert res['count'] == 3
    assert res['score']['accuracy'] == 0.0

def test_score_iris_csv_full():
    model_path = 'tests/fixtures/test_score_actuals/lucas-iris'

    for actuals_path in glob.glob(model_path + '/predictions/*_actuals.feather.zstd'):
        os.remove(actuals_path)

    res = ModelReview({'model_path': model_path}).add_actuals(
      None, actuals_path='tests/fixtures/test_score_actuals/lucas-iris/iris_actuals.csv')

    assert res['accuracy'] == 1.0

@vcr.use_cassette('model_review/score_actuals_no_target/predict.yaml')
def test_score_iris_csv_wo_predicted():
    model_path = 'tests/fixtures/test_score_actuals/lucas-iris'

    for actuals_path in glob.glob(model_path + '/predictions/*_actuals.feather.zstd'):
        os.remove(actuals_path)

    params = _load_score_task_params(model_path)
    ctx = _build_context(params)

    res = ModelReview(params).add_actuals(
      ctx, actuals_path='tests/fixtures/test_score_actuals/lucas-iris/iris_actuals_wo_predictions.csv',
    )

    assert res['accuracy'] == 1.0

def test_score_iris_csv_wo_features():
    model_path = 'tests/fixtures/test_score_actuals/lucas-iris'

    for actuals_path in glob.glob(model_path + '/predictions/*_actuals.feather.zstd'):
        os.remove(actuals_path)

    res = ModelReview({'model_path': model_path}).add_actuals(
      None, actuals_path='tests/fixtures/test_score_actuals/lucas-iris/iris_actuals_wo_features.csv')

    assert res['accuracy'] == 1.0

def test_score_actuals_lucas_case_array_full():
    model_path = 'tests/fixtures/test_score_actuals/lucas-iris'

    for actuals_path in glob.glob(model_path + '/predictions/*_actuals.feather.zstd'):
        os.remove(actuals_path)

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
      None, actual_records=actuals, actual_columns=actual_columns
    )

    assert res['accuracy'] == 1.0

@vcr.use_cassette('model_review/score_actuals_no_target/predict.yaml')
def test_score_actuals_lucas_case_array_wo_prediceted():
    model_path = 'tests/fixtures/test_score_actuals/lucas-iris'

    for actuals_path in glob.glob(model_path + '/predictions/*_actuals.feather.zstd'):
        os.remove(actuals_path)

    actuals = [
      # actual sepal_length sepal_width petal_length petal_width
      [5.1, 3.5, 1.4, 0.2, "setosa"],
    ]

    actual_columns = ["sepal_length", "sepal_width", "petal_length", "petal_width", "actual"]

    params = _load_score_task_params(model_path)
    ctx = _build_context(params)
    res = ModelReview(params).add_actuals(ctx, actual_records=actuals, actual_columns=actual_columns)

    assert res['accuracy'] == 1.0

def test_score_actuals_lucas_case_array_wo_features():
    model_path = 'tests/fixtures/test_score_actuals/lucas-iris'

    for actuals_path in glob.glob(model_path + '/predictions/*_actuals.feather.zstd'):
        os.remove(actuals_path)

    actuals = [
      ["Iris-setosa", "Iris-setosa"],
      ["Iris-setosa", "Iris-setosa"],
      ["Iris-setosa", "Iris-virginica"],
    ]

    actual_columns = ["actual", "class"]

    res = ModelReview({'model_path': model_path}).add_actuals(
      None, actual_records=actuals, actual_columns=actual_columns
    )

    assert res['accuracy'] == 2 / 3

def test_score_actuals_another_result_first():
  model_path = 'tests/fixtures/test_score_actuals/another_result_first'

  for actuals_path in glob.glob(model_path + '/predictions/*_actuals.feather.zstd'):
    os.remove(actuals_path)

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

  res = ModelReview({'model_path': model_path}).add_actuals(None, actual_records=actuals)
  assert res['accuracy'] == 1

def test_build_review_data():
    model_path = 'tests/fixtures/test_score_actuals/lucas-iris'

    res = ModelReview({'model_path': model_path}).build_review_data(
      data_path="tests/fixtures/iris_class_review_B6FD93C248984BC_review_8E0B1F1D71A44DF.csv"
    )
    assert res
    assert res.endswith(".parquet")
    assert 'B6FD93C248984BC' not in res

    res_ar = res.split("_")
    assert len(res_ar) == 4
    assert res_ar[2] == "review"


    for actuals_path in glob.glob('tests/fixtures/iris_class_review_*.parquet'):
      os.remove(actuals_path)

# def test_build_review_data_2():
#     model_path = 'tests/fixtures/test_distribution_chart_stats/bikesharing'

#     res = ModelReview({'model_path': model_path}).build_review_data(
#       data_path="tests/fixtures/bike_sharing_small.csv", date_col='dteday')
#     assert res
#     assert res.endswith(".parquet")

def _build_context(params):
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
