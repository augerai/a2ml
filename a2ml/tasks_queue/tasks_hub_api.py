import celery.signals
import copy
import logging
import json
import time
import traceback

from celery import current_task
from celery.utils.log import get_task_logger
from functools import wraps
from urllib.parse import urlparse

from a2ml.api.a2ml import A2ML
from a2ml.api.a2ml_model import A2MLModel
from a2ml.api.a2ml_experiment import A2MLExperiment
from a2ml.api.a2ml_project import A2MLProject
from a2ml.api.model_review.model_helper import ModelHelper
from a2ml.api.model_review.model_review import ModelReview
from a2ml.api.stats.feature_divergence import FeatureDivergence
from a2ml.api.utils import dict_dig, merge_dicts
from a2ml.api.utils.json_utils import json_dumps_np
from a2ml.api.utils.context import Context
from a2ml.api.utils.s3_fsclient import S3FSClient, BotoClient
from a2ml.tasks_queue.config import Config

from .celery_app import celeryApp

PERSISTENT_DELIVERY_MODE = 2

task_config = Config()
logger = get_task_logger(__name__)

def _log(payload, level=logging.INFO):
    if (level == logging.DEBUG and task_config.debug) or level == logging.INFO:
        logger.info(str(payload))

def _exception_message_chain(e):
    if isinstance(e, Exception) and e.__cause__:
        return str(e) + ' caused by ' + _exception_message_chain(e.__cause__)
    else:
        return str(e)

def _exception_traces_chain(e):
    if isinstance(e, Exception) and e.__cause__:
        ''.join(traceback.format_tb(e.__traceback__)) + '\n\n' + _exception_traces_chain(e.__cause__)
    else:
        return ''.join(traceback.format_tb(e.__traceback__))

def send_result_to_hub(json_data):
    import amqp

    json_data = json_dumps_np(json_data)

    # _log('Send JSON data to Hub: ' + json_data, level=logging.DEBUG)

    o = urlparse(task_config.broker_url)

    connection_params = {
        'host': o.hostname,
        'port': o.port,
        'userid': o.username,
        'password': o.password,
        'virtual_host': o.path.replace('/', '')
    }

    with amqp.Connection(**connection_params) as c:
        channel = c.channel()
        channel.queue_declare(task_config.task_result_queue, durable=True, auto_delete=False)

        channel.basic_publish(
            amqp.Message(json_data, delivery_mode=PERSISTENT_DELIVERY_MODE),
            routing_key=task_config.task_result_queue
        )

def build_and_send_task_result_to_hub(args, status, result, traceback=None):
    if args:
        params = args[0]

        if params and params.get('hub_info', {}).get('cluster_task_id'):
            response = {
                'type': 'TaskResult',
                'provider': params.get('provider'), # provider == None -> means external provider
                'hub_info': params['hub_info'],
                'status': status,
                'runtime': time.time() - current_task.start_time,
                'result': result,
                'traceback': traceback,
            }

            send_result_to_hub(response)

@celery.signals.task_prerun.connect
def celery_task_prerun(**kwargs):
    current_task.start_time = time.time()

def process_task_result(task_func):
    @wraps(task_func)
    def func_wrapper(*args, **kwargs):
        try:
            result = task_func(*args, **kwargs)
            build_and_send_task_result_to_hub(args, 'success', result)
            return result
        except Exception as e:
            build_and_send_task_result_to_hub(
                args,
                'failure',
                _exception_message_chain(e),
                _exception_traces_chain(e)
            )

            # Reraise exception to signal that task is failed
            raise

    return func_wrapper

def _make_hub_provider_info_update(ctx, provider, hub_info):
    #project, project_file, experiment, experiment_session
    project_name = ctx.config.get("name", parts=ctx.config.parts_changes)
    project_file_dataset = ctx.config.get("dataset", parts=ctx.config.parts_changes)
    # project_file_validation_dataset = ctx.config.get("experiment/validation_dataset", parts=ctx.config.parts_changes)

    experiment_name = ctx.config.get('experiment/name', parts=ctx.config.parts_changes)
    experiment_session_id = ctx.config.get('experiment/run_id', parts=ctx.config.parts_changes)

    provider_info = {}

    if project_name:
        provider_info['project'] = {'name': project_name}

    if project_file_dataset:
        provider_info['project_file'] = {'url': project_file_dataset}

    # if project_file_validation_dataset:
    #     if provider_info.get('project_file'):
    #         provider_info['project_file']['validation_dataset'] = project_file_validation_dataset
    #     else:
    #         provider_info['project_file'] = {'validation_dataset': project_file_validation_dataset}

    if experiment_name:
        provider_info['experiment'] = {'name': experiment_name}

    if experiment_session_id:
        provider_info['experiment_session'] = {'id': experiment_session_id}

    return {
        'type': 'ProviderInfoUpdate',
        'hub_info': hub_info,
        'provider': provider,
        'provider_info': {
            provider: provider_info
        }
    }

def _read_hub_experiment_session(ctx, params):
    experiment_session = params['hub_info']['experiment_session']
    provider = params['provider']

    evaluation_options = experiment_session.get('model_settings', {}).get('evaluation_options')
    dataset_statistics = experiment_session.get('dataset_statistics', {}).get('stat_data', [])

    ctx.config.set('model_type',
        "classification" if evaluation_options.get('classification', True) else "regression")
    _get_options_from_dataset_statistic(ctx.config, dataset_statistics)

    ctx.config.set('experiment/validation_source', evaluation_options.get('test_data_path'))

    ctx.config.set('experiment/cross_validation_folds',
        evaluation_options.get('crossValidationFolds', 5))
    split_options = evaluation_options.get('splitOptions', {})
    if split_options.get('trainRatio'):
        ctx.config.set('experiment/validation_size', 1.0-float(split_options.get('trainRatio')))
    if split_options.get('shuffleData'):
        ctx.config.set('experiment/shuffle', split_options.get('shuffleData'))
    if split_options.get('timeseriesSplit'):
        ctx.config.set('experiment/timeseries_fold_split', split_options.get('timeseriesSplit'))

    ctx.config.set('experiment/max_total_time',
        evaluation_options.get('max_total_time_mins', 60))

    ctx.config.set('experiment/max_cores_per_trial',
        evaluation_options.get('cpu_per_mt_algorithm', 1))
    ctx.config.set('experiment/max_concurrent_trials',
        evaluation_options.get('trials_per_worker', 1))

    ctx.config.set('experiment/max_eval_time',
        evaluation_options.get('max_eval_time_mins', 6))
    ctx.config.set('experiment/max_n_trials',
        evaluation_options.get('max_n_trials', 100))
    ctx.config.set('experiment/use_ensemble',
        evaluation_options.get('use_ensemble', True))
    ctx.config.set('experiment/metric', evaluation_options.get('scoring'))

    if evaluation_options.get('algorithms_to_exlude'):
        ctx.config.set('experiment/blocked_models', evaluation_options.get('algorithms_to_exlude'))
    if evaluation_options.get('allowed_algorithms'):
        ctx.config.set('experiment/allowed_models', evaluation_options.get('allowed_algorithms'))
    if evaluation_options.get('exit_score'):
        ctx.config.set('experiment/exit_score', evaluation_options.get('exit_score'))
    if evaluation_options.get('score_top_count'):
        ctx.config.set('experiment/score_top_count', evaluation_options.get('score_top_count'))

    return ctx

def _update_hub_objects(ctx, provider, params):
    hub_objects_update = _make_hub_provider_info_update(ctx, params.get('provider'), params.get('hub_info'))
    send_result_to_hub(hub_objects_update)

    return hub_objects_update

def _get_options_from_dataset_statistic(config, stat_data):
    excluded_features = []
    target_feature = None

    categoricals = []
    label_encoded = []
    time_series = []
    date_time = []

    for item in stat_data:
        if item.get('isTarget'):
            target_feature = item['column_name']

        if not item.get('use') and not item.get('isTarget'):
            excluded_features.append(item['column_name'])

        if item.get('use') or item.get('isTarget'):
            if item['datatype'] == 'categorical':
                categoricals.append(item['column_name'])
            if item['datatype'] == 'hashing':
                categoricals.append(item['column_name'])
                label_encoded.append(item['column_name'])
            if item['datatype'] == 'timeseries':
                time_series.append(item['column_name'])
            if item['datatype'] == 'datetime':
                date_time.append(item['column_name'])

    if target_feature:
        config.set('target', target_feature)
    if excluded_features:
        config.set('exclude', excluded_features)

    if label_encoded:
        config.set('experiment/label_encoded', label_encoded)
    if categoricals:
        config.set('experiment/categoricals', categoricals)
    if date_time:
        config.set('experiment/date_time', date_time)
    if time_series:
        config.set('experiment/time_series', time_series)

def execute_task(task, params, wait_for_result=False, delay=0):
    if wait_for_result:
        task.apply(args=[params], countdown = delay)
    else:
        task.apply_async(args=[params], countdown = delay)

def _format_leaderboard_for_hub(leaderboard):
    formatted_leaderboard_list = []

    for item in leaderboard:
        obj = {}
        uid = item['uid']
        obj[uid] = item
        formatted_leaderboard_list.append(obj)

    return formatted_leaderboard_list

def _update_hub_leaderboad(params, leaderboard):
    from a2ml.api.auger.experiment import AugerExperiment

    ctx = Context(debug=task_config.debug)
    experiment = AugerExperiment(ctx)
    _log(leaderboard, level=logging.DEBUG)

    data = {
        'type': 'Leaderboard',
        'provider': params['provider'],
        'hub_info': params['hub_info'],
        'trials': _format_leaderboard_for_hub(leaderboard.get('trials', [])),
        'evaluate_status': leaderboard.get('evaluate_status'),
    }

    send_result_to_hub(data)

def _create_provider_context(params):
    provider = params.get('provider', 'auger')

    ctx = Context(
        name=provider,
        path=params.get('hub_info', {}).get('project_path'),
        debug=task_config.debug
    )

    if provider == 'auger':
        auger_creds = params.get('auger_creds', None)
        if auger_creds:
            ctx.credentials = auger_creds

    ctx.set_runs_on_server(True)
    ctx.config.set('providers', [provider])

    hub_info = params.get('hub_info', {})
    provider_info = params.get('provider_info', {}).get(provider, {})
    project_name = dict_dig(provider_info, 'project', 'name') or hub_info.get('project_name')
    experiment_name = dict_dig(provider_info, 'experiment', 'name') or hub_info.get('experiment_name')

    if project_name:
        ctx.config.set('name', project_name, provider)
    if experiment_name:
        ctx.config.set('experiment/name', experiment_name, provider)
    if provider_info.get('experiment_session', {}).get('id'):
        ctx.config.set('experiment/run_id', provider_info['experiment_session']['id'], provider)
    if hub_info.get('experiment_session') and hub_info.get('experiment_session').get('id'):
        ctx.config.set('experiment/hub_session_id', hub_info['experiment_session']['id'], provider)
        ctx.config.set('experiment/hub_experiment_id', hub_info['experiment_session'].get('experiment_id'), provider)

    return ctx

def _get_leaderboad(params):
    ctx = _create_provider_context(params)
    provider = params['provider']

    res = A2ML(ctx).evaluate()
    _log(res, level=logging.DEBUG)

    if res.get(provider, {}).get('result'):
        data = res[provider]['data']
        leaderboard = data['leaderboard']
        status = data['status']
        trials_count = data.get('trials_count', 0)

        trials = []

        for item in leaderboard:
            score = item['all_scores'].get(item['primary_metric'])
            if score is None:
                ctx.log('Leaderboard item does not contain primary score: %s'%item)
                score = 0.0

            trials.append({
                "uid": item['model id'],
                "score": score,
                "scoring": item['primary_metric'],
                "ensemble": 'Ensemble' in item['algorithm'],
                "task_type": item['task_type'],
                "all_scores": item['all_scores'],
                "score_name": item['primary_metric'],
                "algorithm_name": item['algorithm_name'],
                "optimizer_name": "Azure",
                "evaluation_time": float(item["fit_time"]),
                "algorithm_params": item['algorithm_params'],
                "experiment_session_id": ctx.config.get('experiment/run_id'),
                "preprocessor": item["preprocessor"],
                "algorithm_params_hash": None, #TODO : make_algorithm_params_hash in auger-ml

                "error": None,
                "ratio": 1.0,
                "budget": None,
                "create_trial_time": None,
                "estimated_time": 0,
                "estimated_timeout": False,
                "trialClass": None,
                "fold_scores": [],
                "fold_times": [],
                "metrics_time": 0,
                "dataset_ncols": 0,
                "dataset_nrows": 0,
                "dataset_manifest_id": None,
            })

        evaluate_status = {
            'status': status,
            'completed_evaluations': trials_count,
            'errors' : {'error': data.get('error'), 'error_details': data.get('error_details')}
        }

        return {
            'evaluate_status': evaluate_status,
            'trials': trials,
        }

@celeryApp.task(ignore_result=True)
@process_task_result
def monitor_evaluate_task(params):
    leaderboard = _get_leaderboad(params)

    if leaderboard:
        _update_hub_leaderboad(params, leaderboard)

    return True

@celeryApp.task(ignore_result=True)
@process_task_result
def evaluate_start_task(params):
    if not params.get('hub_info', {}).get('experiment_session_id'):
        raise Exception("evaluate_start_task missed experiment_session_id parameter.")

    ctx = _create_provider_context(params)
    provider = params.get('provider', 'auger')
    provider_info = params.get('provider_info', {}).get(provider, {})
    ctx.config.set('dataset', provider_info.get('project_file').get('url'), provider)

    cluster = provider_info.get('project', {}).get('cluster', {})
    ctx.config.set('cluster/name', cluster.get('name'), provider)
    ctx.config.set('cluster/min_nodes', cluster.get('min_nodes'), provider)
    ctx.config.set('cluster/max_nodes', cluster.get('max_nodes'), provider)
    ctx.config.set('cluster/type', cluster.get('type'), provider)

    ctx = _read_hub_experiment_session(ctx, params)
    ctx.config.clean_changes()

    res = A2ML(ctx).train()

    _update_hub_objects(ctx, provider, params)

    return res

@celeryApp.task(ignore_result=True)
@process_task_result
def stop_evaluate_task(params):
    ctx = _create_provider_context(params)

    ctx.config.clean_changes()
    res = A2MLExperiment(ctx).stop()
    _update_hub_objects(ctx, params.get('provider'), params)

    return res

@celeryApp.task(ignore_result=True)
@process_task_result
def update_cluster_config_task(params):
    ctx = _create_provider_context(params)
    clusters = params.get('clusters', [])
    for cluster in clusters:
        ctx.config.set('cluster/name', cluster.get('name'))
        res = A2MLProject(ctx).update_cluster_config(name=None, params=cluster)

    return True

@celeryApp.task(ignore_result=True)
@process_task_result
def import_data_task(params):
    if not params.get('hub_info').get('project_file'):
        raise Exception("import_data_task missed project_file parameter.")

    project_file = params['hub_info']['project_file']

    data_path = params.get('url')
    if not data_path:
        data_path = project_file.get('url')

    ctx = _create_provider_context(params)

    ctx.config.clean_changes()
    res = A2ML(ctx).import_data(source=data_path)
    _update_hub_objects(ctx, params.get('provider'), params)

    return res

@celeryApp.task(ignore_result=True)
@process_task_result
def deploy_model_task(params):
    ctx = _create_provider_context(params)
    provider = params.get('provider', 'auger')
    provider_info = params.get('provider_info', {}).get(provider, {})

    deploy_cluster = provider_info.get('project', {}).get('deploy_cluster', {})
    ctx.config.set('deploy_cluster/type', deploy_cluster.get('type'), provider)
    ctx.config.set('deploy_cluster/memory_gb', deploy_cluster.get('memory_gb'), provider)
    ctx.config.set('deploy_cluster/cpu_cores', deploy_cluster.get('cpu_cores'), provider)
    ctx.config.set('deploy_cluster/compute_target', deploy_cluster.get('compute_target'), provider)

    ctx = _read_hub_experiment_session(ctx, params)

    ctx.config.clean_changes()
    res = A2ML(ctx).deploy(model_id = params.get('model_id'), review = params.get('support_review_model'),
        locally=params.get('locally', False))
    _update_hub_objects(ctx, params.get('provider'), params)

    return res

@celeryApp.task(ignore_result=True)
@process_task_result
def add_external_model_task(params):
    return ModelReview(params).add_external_model(
        target_column=params.get('target_column'),
        scoring=params.get('scoring'),
        task_type=params.get('task_type'),
        binary_classification=params.get('binary_classification', False),
    )

@celeryApp.task(ignore_result=True)
@process_task_result
def undeploy_model_task(params):
    ctx = _create_provider_context(params)
    provider = params.get('provider', 'auger')

    model_id = params.get('hub_info', {}).get('pipeline_id')
    if not model_id:
        model_id = params.get('model_id')

    if not model_id:
        raise Exception("undeploy_model_task: hub_info/pipeline_id should be provided.")

    ctx.config.set('undeploy/service_only', params.get('service_only', False), provider)
    res = A2MLModel(ctx).undeploy(model_id = model_id, locally=params.get('locally', False))

    return res

@celeryApp.task(ignore_result=True)
@process_task_result
def predict_by_model_task(params):
    from a2ml.api.utils.crud_runner import CRUDRunner

    ctx = _create_provider_context(params)
    ctx = _read_hub_experiment_session(ctx, params)
    ctx.config.clean_changes()

    runner = CRUDRunner(ctx, "%s"%params.get('provider'), 'model')
    res = list(runner.providers.values())[0].predict(
        filename=params.get('path_to_predict'),
        model_id=params.get('model_id'),
        threshold=params.get('threshold'),
        data=params.get('records'),
        columns=params.get('features'),
        json_result=params.get('json_result'),
        count_in_result=params.get('count_in_result'),
        predicted_at=params.get('prediction_date'),
        prediction_id = params.get('prediction_id'),
        locally = params.get('locally', False)
    )
    _update_hub_objects(ctx, params.get('provider'), params)

    return res['predicted']

@celeryApp.task(ignore_result=True)
@process_task_result
def score_actuals_by_model_task(params):
    ctx = None
    external_model = params.get("external_model", False)

    if not external_model:
        ctx = _create_provider_context(params)
        ctx = _read_hub_experiment_session(ctx, params)
        ctx.config.clean_changes()

    return ModelReview(params).add_actuals(
        ctx,
        actuals_path = params.get('actuals_path'),
        data=params.get('actual_records'),
        columns=params.get('actual_columns', None),
        actual_date=params.get('actual_date'),
        actual_date_column=params.get('actual_date_column'),
        actuals_id=params.get('actuals_id'),
        return_count=params.get('return_count', False),
        provider=params.get('provider'),
        external_model=external_model,
    )

@celeryApp.task(ignore_result=True)
@process_task_result
def delete_actuals_task(params):
    return ModelReview(params).delete_actuals(
        with_predictions=params.get('with_predictions'),
        begin_date=params.get('begin_date'),
        end_date=params.get('end_date'),
    )

@celeryApp.task(ignore_result=True)
@process_task_result
def score_model_performance_daily_task(params):
    return ModelReview(params).score_model_performance_daily(
        date_from=params.get('date_from'),
        date_to=params.get('date_to'),
    )

@celeryApp.task(ignore_result=True)
@process_task_result
def set_support_review_model_flag_task(params):
    return ModelReview(params).set_support_review_model_flag(
        flag_value=params.get('support_review_model')
    )

@celeryApp.task(ignore_result=True)
@process_task_result
def distribution_chart_stats_task(params):
    return ModelReview(params).distribution_chart_stats(
        date_from=params.get('date_from'),
        date_to=params.get('date_to'),
    )

@celeryApp.task(ignore_result=True)
@process_task_result
def remove_model_task(params):
    return ModelReview(params).remove_model()

@celeryApp.task(ignore_result=True)
@process_task_result
def clear_model_results_and_actuals(params):
    return ModelReview(params).clear_model_results_and_actuals()

@celeryApp.task(ignore_result=True)
@process_task_result
def build_review_data_task(params):
    ctx = _create_provider_context(params)
    ctx = _read_hub_experiment_session(ctx, params)

    date_col = None
    if ctx.config.get_list('experiment/date_time'):
        date_col = ctx.config.get_list('experiment/date_time')[0]

    return ModelReview(params).build_review_data(
        data_path=params.get('data_path'),
        date_col = date_col
    )

@celeryApp.task(ignore_result=True)
@process_task_result
def build_divergence_model_task(params):
    return FeatureDivergence(params).build_and_save_model()

@celeryApp.task(ignore_result=True)
@process_task_result
def calc_divergence_daily_task(params):
    # In casse of ModelIsNotReadyError try to build it and retry 1 time
    for attempt in range(2):
        try:
            return FeatureDivergence(params).score_divergence_daily(
                date_from=params.get('date_from'),
                date_to=params.get('date_to'),
                top_n=params.get('top_n'),
            )
        except FeatureDivergence.ModelIsNotReadyError as e:
            if attempt == 0:
                FeatureDivergence(params).build_and_save_model()
            else:
                raise e

@celeryApp.task(ignore_result=True)
@process_task_result
def create_org_bucket(params):
    client = S3FSClient()
    client.ensure_bucket_created(
        Bucket=params['bucket_name'],
        region=params.get('region')
    )

    return True

@celeryApp.task(ignore_result=True)
@process_task_result
def delete_org_bucket(params):
    client = S3FSClient()
    client.ensure_bucket_deleted(Bucket=params['bucket_name'])

    return True

@celeryApp.task(ignore_result=True)
@process_task_result
def presign_s3_url_task(params):
    client = BotoClient(region=params.get('region'))

    path = params.get('path')
    if path:
        params['bucket'], params['key'] = S3FSClient.split_path_to_bucket_and_key(path)

    if params.get('multipart', False):
        return client.get_multipart_upload_config(
            bucket=params['bucket'],
            key=params['key'],
            expires_in=params.get('expires_in'),
        )
    else:
        return client.generate_presigned_url_ex(
            bucket=params['bucket'],
            key=params['key'],
            method=params['method'],
            expires_in=params.get('expires_in'),
            max_content_length=params.get('max_content_length'),
        )

@celeryApp.task(ignore_result=True)
@process_task_result
def validate_roi_syntax_task(params):
    return ModelReview(params).validate_roi_syntax(
        expressions=params["expressions"],
    )
