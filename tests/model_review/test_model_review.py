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


def test_count_actuals_by_prediction_id():
    model_path = 'tests/fixtures/test_count_actuals_by_prediction_id/adult'
    res = ModelReview({'model_path': model_path}).count_actuals_by_prediction_id()

    assert type(res) is dict
    assert len(res) > 0

    assert res == {
      'ffa89d52-5300-412d-b7a4-d21b3c9b7d16': 2,
      '5d9f640d-529a-42bd-be85-172107249a01': 1,
      '066f3c25-80ee-4c75-af15-38cda8a4ad57': 1
    }

def test_count_actuals_by_prediction_id_with_period():
    model_path = 'tests/fixtures/test_count_actuals_by_prediction_id/adult'
    date_from = datetime.date(2020, 8, 18)
    date_to = datetime.date(2020, 8, 18)
    res = ModelReview({'model_path': model_path}).count_actuals_by_prediction_id(date_from, date_to)

    assert type(res) is dict
    assert len(res) > 0

    assert res == {
      'ffa89d52-5300-412d-b7a4-d21b3c9b7d16': 1,
      '5d9f640d-529a-42bd-be85-172107249a01': 1,
      '066f3c25-80ee-4c75-af15-38cda8a4ad57': 1
    }

def test_score_model_performance_daily():
    model_path = 'tests/fixtures/test_score_model_performance_daily/iris'
    date_from = datetime.date(2020, 2, 16)
    date_to = datetime.date(2020, 2, 18)

    res = ModelReview({'model_path': model_path}).score_model_performance_daily(str(date_from), date_to)
    assert type(res) is dict
    assert type(res[str(date_from)]) is numpy.float64
    assert res[str(date_from)] > 0

# def test_rename_target():
#     model_paths = [
#       # 'tests/fixtures/test_score_model_performance_daily/iris_no_matches',
#       # 'tests/fixtures/test_score_model_performance_daily/iris',
#       #'tests/fixtures/test_score_model_performance_daily/iris_not_full_actuals', #class
#       'tests/fixtures/test_score_actuals', #income
#       # 'tests/fixtures/test_score_actuals/pr_can/candidate'
#     ]
#     for model_path in model_paths:
#       files = fsclient.list_folder(os.path.join(model_path, "predictions/*_actuals.feather.zstd"),
#         wild=True, remove_folder_name=False, meta_info=False)

#       for (file, ds) in DataFrame.load_from_files(files):
#         ds.df.rename(columns={'actual': 'income'}, inplace=True)
#         ds.saveToFile(file)

def test_score_model_performance_daily_no_matching_actuals_and_predictions():
    model_path = 'tests/fixtures/test_score_model_performance_daily/iris_no_matches'
    date_from = datetime.date(2020, 2, 16)
    date_to = datetime.date(2020, 2, 18)

    res = ModelReview({'model_path': model_path}).score_model_performance_daily(date_from, str(date_to))
    assert type(res) is dict
    assert res[str(date_from)] == 0

def test_score_model_performance_daily_not_full_actuals():
    model_path = 'tests/fixtures/test_score_model_performance_daily/iris_not_full_actuals'
    date_from = datetime.date(2020, 3, 12)
    date_to = datetime.date(2020, 3, 13)

    res = ModelReview({'model_path': model_path}).score_model_performance_daily(date_from, str(date_to))
    assert type(res) is dict
    assert res[str(date_to)] == 0

def load_metric_task_params(model_path):
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

def test_distribution_chart_stats():
    model_path = 'tests/fixtures/test_distribution_chart_stats/bikesharing'
    date_from = datetime.date(2020, 2, 16)
    date_to = datetime.date(2020, 2, 19)

    res = ModelReview(load_metric_task_params(model_path)).distribution_chart_stats(date_from, date_to)
    assert type(res) is dict
    assert type(res[str(date_to)]) is dict

    assert res[str(date_to)] == {
      'cnt': { 'avg': 483.18357849636016, 'std_dev': 0.0, 'imp': 0 },
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
      'a2ml_actual': { 'avg': 2.6, 'std_dev': 2.073644135332772, 'imp': 0 },
    }

def test_distribution_chart_stats_for_categorical_target():
    model_path = 'tests/fixtures/test_distribution_chart_stats/adult'
    date_from = datetime.date(2020, 2, 16)
    date_to = datetime.date(2020, 2, 20)

    res = ModelReview(load_metric_task_params(model_path)).distribution_chart_stats(date_from, date_to)
    assert type(res) is dict
    assert type(res[str(date_to)]) is dict

    assert res[str(date_to)] == {
      'income': {'dist': {' <=50K': 1}, 'imp': 0},
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
      'a2ml_actual': {'dist': {' <=50K': 1}, 'imp': 0},
    }

def test_distribution_chart_stats_with_null_booleans():
    model_path = 'tests/fixtures/test_distribution_chart_stats/callouts'
    date_from = datetime.date(2020, 5, 7)
    date_to = datetime.date(2020, 5, 7)

    res = ModelReview(load_metric_task_params(model_path)).distribution_chart_stats(date_from, date_to)
    assert type(res) is dict
    assert type(res[str(date_to)]) is dict

    assert res[str(date_to)] == {
      'target': {'avg': 0.5, 'std_dev': 0.7071067811865476, 'imp': 0},
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

    params = load_metric_task_params(model_path)

    res = ModelReview(params)._get_feature_importances()
    assert res == {'workclass': 0.12006373015194421, 'sex': 0.039481754114499897,
      'occupation': 0.20967661413259162, 'education': 0.2999579889231273,
      'relationship': 0.08698243068672135, 'marital-status': 0.14329620992107325,
      'race': 0.04180630794271793, 'native-country': 0.02072552576600564,
      'capital-loss': 0.2571256791934569, 'capital-gain': 0.31323744185565716,
      'hours-per-week': 0.4246393312722869, 'age': 0.7161049235052714, 'fnlwgt': 1.0}

def test_get_feature_importances_no_metrics_cache():
    model_path = 'tests/fixtures/test_distribution_chart_stats/adult'

    params = load_metric_task_params(model_path)
    params['hub_info']['pipeline_id'] = '555555555555555'

    res = ModelReview(params)._get_feature_importances()

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

def test_score_actuals_with_not_full_actuals():
    model_path = 'tests/fixtures/test_score_actuals'

    for actuals_path in glob.glob(model_path + '/predictions/*_actuals.feather.zstd'):
      os.remove(actuals_path)

    actuals = [
      {'prediction_id': '5c93079c-00c9-497a-8967-53fa0dd02054', 'actual': False },
      {'prediction_id': 'b1bf9ebf-0277-4771-9bc5-236690a21194', 'actual': False },
      {'prediction_id': 'f61b1bbc-6f7b-4e7e-9a3b-6acb6e1462cd', 'actual': True },
    ]

    actual_date = datetime.date.today() - datetime.timedelta(days=1)

    res = ModelReview({'model_path': model_path}).add_actuals(
      actuals_path=None, actual_records=actuals, actual_date=actual_date
    )
    actual_files = glob.glob(model_path + '/predictions/*_actuals.feather.zstd')
    assert len(actual_files) > 0
    assert str(actual_date) in actual_files[0]

    stored_actuals = DataFrame({})
    stored_actuals.loadFromFeatherFile(actual_files[0])
    assert 'prediction_group_id' in stored_actuals.columns

    stored_actuals = json.loads(
      stored_actuals.df.sort_values(by=['prediction_id']).to_json(orient='records')
    )

    assert len(stored_actuals) == len(actuals) #+ 1

    assert stored_actuals[0]['prediction_id'] == '5c93079c-00c9-497a-8967-53fa0dd02054'
    assert stored_actuals[0]['prediction_group_id'] == '2ab1e430-6082-4465-b057-3408d36de144'
    assert stored_actuals[0]['feature1'] == 1
    assert stored_actuals[0]['income'] == False

    assert stored_actuals[1]['prediction_id'] == 'b1bf9ebf-0277-4771-9bc5-236690a21194'
    assert stored_actuals[1]['prediction_group_id'] == '2ab1e430-6082-4465-b057-3408d36de144'
    assert stored_actuals[1]['feature1'] == 1.1
    assert stored_actuals[1]['income'] == False

    assert stored_actuals[2]['prediction_id'] == 'f61b1bbc-6f7b-4e7e-9a3b-6acb6e1462cd'
    assert stored_actuals[2]['prediction_group_id'] == '03016c26-f69a-416f-817f-4c58cd69d675'
    assert stored_actuals[2]['feature1'] == 1.3
    assert stored_actuals[2]['income'] == True

def test_score_actuals_return_count():
    model_path = 'tests/fixtures/test_score_actuals'

    for actuals_path in glob.glob(model_path + '/predictions/*_actuals.feather.zstd'):
      os.remove(actuals_path)

    actuals = [
      {'prediction_id': '5c93079c-00c9-497a-8967-53fa0dd02054', 'actual': True },
      {'prediction_id': 'b1bf9ebf-0277-4771-9bc5-236690a21194', 'actual': False },
      {'prediction_id': 'f61b1bbc-6f7b-4e7e-9a3b-6acb6e1462cd', 'actual': False },
    ]

    res = ModelReview({'model_path': model_path}).add_actuals(
      actuals_path=None, actual_records=actuals, return_count=True
    )

    assert res['count'] == 3
    assert res['score']['accuracy'] == 1.0

def test_score_actuals_return_count_nones():
    model_path = 'tests/fixtures/test_score_actuals'

    for actuals_path in glob.glob(model_path + '/predictions/*_actuals.feather.zstd'):
      os.remove(actuals_path)

    actuals = [
      {'prediction_id': '5c93079c-00c9-497a-8967-53fa0dd02054', 'actual': None },
      {'prediction_id': 'b1bf9ebf-0277-4771-9bc5-236690a21194', 'actual': None },
      {'prediction_id': 'f61b1bbc-6f7b-4e7e-9a3b-6acb6e1462cd', 'actual': None },
    ]

    res = ModelReview({'model_path': model_path}).add_actuals(
      actuals_path=None, actual_records=actuals, return_count=True
    )

    assert res['count'] == 3
    assert res['score']['accuracy'] == 0.0

def test_build_review_data():
    model_path = 'tests/fixtures/test_score_actuals/lucas-iris'

    res = ModelReview({'model_path': model_path}).build_review_data(data_path="tests/fixtures/iris_class.csv")
    assert res

def test_score_actuals_lucas_case():
    model_path = 'tests/fixtures/test_score_actuals/lucas-iris'

    for actuals_path in glob.glob(model_path + '/predictions/*_actuals.feather.zstd'):
        os.remove(actuals_path)

    actuals = [
      { 'actual': 'Iris-setosa', 'prediction_id': 'eaed9cd8-ba49-4c06-86d5-71d453c681d1' },
      { 'actual': 'Iris-setosa', 'prediction_id': '2be58239-3508-41e3-921d-28be50319bdc' },
      { 'actual': 'Iris-setosa', 'prediction_id': 'bc25e14e-76b0-4082-84a3-9e1684916088' },
      { 'actual': 'Iris-setosa', 'prediction_id': '55764866-56df-402a-8f8b-f713c2c9fbc2' },
      { 'actual': 'Iris-setosa', 'prediction_id': 'e93b9605-ed74-42cb-86f2-64f619be9139' },
      { 'actual': 'Iris-setosa', 'prediction_id': '316852e1-a6eb-4740-92b2-69a4b27667d9' },
      { 'actual': 'Iris-setosa', 'prediction_id': '7e641ffd-bb06-4a18-aad6-db416bf55bfb' },
      { 'actual': 'Iris-setosa', 'prediction_id': '5ac7274b-d094-43e8-8947-c4705f13eb97' },
      { 'actual': 'Iris-setosa', 'prediction_id': 'f1dd6088-8d70-43e3-bf84-bebf14eaa3b6' }
    ]

    res = ModelReview({'model_path': model_path}).add_actuals(actuals_path=None, actual_records=actuals,
      calc_score=True)

    assert res == {
      'accuracy': 1.0,
      'neg_log_loss': 0,
      'f1_micro': 1.0,
      'f1_macro': 1.0,
      'f1_weighted': 1.0,
      'precision_micro': 1.0,
      'precision_macro': 1.0,
      'precision_weighted': 1.0,
      'recall_micro': 1.0,
      'recall_macro': 1.0,
      'recall_weighted': 1.0
    }

def test_score_actuals_lucas_case_array():
    model_path = 'tests/fixtures/test_score_actuals/lucas-iris'

    for actuals_path in glob.glob(model_path + '/predictions/*_actuals.feather.zstd'):
        os.remove(actuals_path)

    actuals = [
      ['eaed9cd8-ba49-4c06-86d5-71d453c681d1', 'Iris-setosa'],
      ['2be58239-3508-41e3-921d-28be50319bdc', 'Iris-setosa'],
      ['bc25e14e-76b0-4082-84a3-9e1684916088', 'Iris-setosa'],
      ['55764866-56df-402a-8f8b-f713c2c9fbc2', 'Iris-setosa'],
      ['e93b9605-ed74-42cb-86f2-64f619be9139', 'Iris-setosa'],
      ['316852e1-a6eb-4740-92b2-69a4b27667d9', 'Iris-setosa'],
      ['7e641ffd-bb06-4a18-aad6-db416bf55bfb', 'Iris-setosa'],
      ['5ac7274b-d094-43e8-8947-c4705f13eb97', 'Iris-setosa'],
      ['f1dd6088-8d70-43e3-bf84-bebf14eaa3b6', 'Iris-setosa']
    ]

    res = ModelReview({'model_path': model_path}).add_actuals(actuals_path=None, actual_records=actuals,
      calc_score=True)

    assert res == {
      'accuracy': 1.0,
      'neg_log_loss': 0,
      'f1_micro': 1.0,
      'f1_macro': 1.0,
      'f1_weighted': 1.0,
      'precision_micro': 1.0,
      'precision_macro': 1.0,
      'precision_weighted': 1.0,
      'recall_micro': 1.0,
      'recall_macro': 1.0,
      'recall_weighted': 1.0
    }

def test_score_actuals_with_no_predictions_in_model_folder():
    model_path = 'tests/fixtures/test_score_actuals/iris'

    for actuals_path in glob.glob(model_path + '/predictions/*_actuals.feather.zstd'):
      os.remove(actuals_path)

    actuals = [
      { 'prediction_id':'09aaa96b-5d9c-4c45-ab04-726da868624b', 'actual':'versicolor' },
      { 'prediction_id':'5e5ad22b-6789-47c6-9a4d-a3a998065127', 'actual':'virginica' }
    ]

    try:
      ModelReview({'model_path': model_path}).add_actuals(actuals_path=None, actual_records=actuals)
    except Exception as e:
      assert 'there is no prediction results for this model' in str(e)
    else:
      fail('No exception was raised')

    actual_files = glob.glob(model_path + '/predictions/*_actuals.feather.zstd')
    assert len(actual_files) == 0

def test_score_actuals_for_candidate_prediction():
  # Prediction data:
  # { 'prediction_id':'bef9be07-5534-434e-ab7c-c379d8fcfe77', 'species':'versicolor' },
  # { 'prediction_id':'f61b1bbc-6f7b-4e7e-9a3b-6acb6e1462cd', 'species':'virginica' }
  model_path = 'tests/fixtures/test_score_actuals/pr_can/candidate'
  prediction_group_id = '272B088D17A7490'

  # Primary prediction data:
  # { 'prediction_id':'09aaa96b-5d9c-4c45-ab04-726da868624b', 'species':'virginica' },
  # { 'prediction_id':'5e5ad22b-6789-47c6-9a4d-a3a998065127', 'species':'virginica' }
  primary_model_path = 'tests/fixtures/test_score_actuals/pr_can/primary'
  primary_prediction_group_id = 'A4FD5B64FEE5434'

  for actuals_path in glob.glob(model_path + '/predictions/*_actuals.feather.zstd'):
      os.remove(actuals_path)

  actuals = [
    { 'prediction_id':'09aaa96b-5d9c-4c45-ab04-726da868624b', 'actual':'versicolor' },
    { 'prediction_id':'5e5ad22b-6789-47c6-9a4d-a3a998065127', 'actual':'virginica' }
  ]

  res = ModelReview({'model_path': model_path}).add_actuals(
    actual_records=actuals, prediction_group_id=prediction_group_id,
    primary_prediction_group_id=primary_prediction_group_id, primary_model_path=primary_model_path,
    calc_score=True
  )

  assert type(res) == dict
  assert res['accuracy'] == 1.0

  actual_files = glob.glob(model_path + '/predictions/*_actuals.feather.zstd')
  assert len(actual_files) == 1
  actual_file = actual_files[0]
  assert str(datetime.date.today()) in actual_file

  stored_actuals = DataFrame({})
  stored_actuals.loadFromFeatherFile(actual_file)
  assert 'prediction_group_id' in stored_actuals.columns

  stored_actuals = json.loads(
    stored_actuals.df.sort_values(by=['prediction_id']).to_json(orient='records')
  )

  assert stored_actuals[0]['prediction_id'] == 'bef9be07-5534-434e-ab7c-c379d8fcfe77'
  assert stored_actuals[0]['prediction_group_id'] == prediction_group_id
  assert stored_actuals[0]['species'] == 'versicolor'

  assert stored_actuals[1]['prediction_id'] == 'f61b1bbc-6f7b-4e7e-9a3b-6acb6e1462cd'
  assert stored_actuals[1]['prediction_group_id'] == prediction_group_id
  assert stored_actuals[1]['species'] == 'virginica'

def test_score_actuals_another_result_first():
  model_path = 'tests/fixtures/test_score_actuals/another_result_first'

  for actuals_path in glob.glob(model_path + '/predictions/*_actuals.feather.zstd'):
    os.remove(actuals_path)

  actuals = [
    { 'prediction_id':'df3fdbfd-688c-4c93-8211-ffd8b68ccaa7', 'actual':'good' },
  ]

  res = ModelReview({'model_path': model_path}).add_actuals(actual_records=actuals, calc_score=True)
  assert res['accuracy'] == 1

