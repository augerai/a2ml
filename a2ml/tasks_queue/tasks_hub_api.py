from .celery_app import celeryApp
import copy

from a2ml.api.model_review.model_review import ModelReview
from a2ml.api.model_review.model_helper import ModelHelper

def _exception_message_with_all_causes(e):
    if isinstance(e, Exception) and e.__cause__:
        return str(e) + ' caused by ' + __exception_message_with_all_causes(e.__cause__)
    else:
        return str(e)

def process_task_result(status, retval, task_id, args, kwargs, einfo):
    #logging.info("process_task_result exception: %s"%(einfo))
    if args:
        params = args[0]

        if params and params.get('augerInfo', {}).get('cluster_task_id'):
            if isinstance(retval, Exception):
                retval = _exception_message_with_all_causes(retval)
                # newrelic.agent.record_exception(
                #     exc=retval,
                #     params={'status': status, 'task_id': task_id, 'args': args, 'kwargs': kwargs}
                # )

            #TODO: update cluster_task    
            # AugerMessenger(params).set_cluster_task_result(params['augerInfo']['cluster_task_id'],
            #     status, retval, str(einfo))

def _get_experiment_session(params):
    from a2ml.api.utils.context import Context
    from a2ml.api.auger.experiment import AugerExperiment
    from a2ml.api.auger.impl.cloud.experiment_session import AugerExperimentSessionApi

    if not params.get('augerInfo', {}).get('experiment_session_id'):
        raise Exception("evaluate_start_task missed experiment_session_id parameter.")

    ctx = Context(
        #path=params.get('project_path'),
        debug=params.get('debug_log', True)
    )

    ctx.credentials = params.get('provider_info', {}).get('auger', {}).get('credentials')
    experiment_api = AugerExperiment(ctx)

    session_api = AugerExperimentSessionApi(ctx, experiment_api, None, 
        params['augerInfo']['experiment_session_id'])
    return session_api.properties()

@celeryApp.task(ignore_result=False, after_return=process_task_result)
def evaluate_start_task(params):
    from a2ml.api.utils.context import Context
    from a2ml.api.a2ml import A2ML

    experiment_session = _get_experiment_session(params)    

    ctx = Context(
        #path=params.get('project_path'),
        debug=params.get('debug_log', True)
    )
    ctx.set_runs_on_server(True)

    #TODO: support validation_source
    provider_info = params.get('provider_info', {}).get(params.get('provider'), {})
    ctx.config.set('providers', [params.get('provider')])
    ctx.credentials = provider_info.get('credentials')

    ctx.config.set('dataset', provider_info.get('dataset'), params.get('provider'))
    ctx.config.set('name', provider_info.get('project').get('name'), params.get('provider'))
    ctx.config.set('experiment/name', provider_info.get('experiment').get('name'), params.get('provider'))
    ctx.config.set('cluster/name', provider_info.get('cluster').get('name'), params.get('provider'))
    ctx.config.set('cluster/min_nodes', provider_info.get('cluster').get('min_nodes'), params.get('provider'))
    ctx.config.set('cluster/max_nodes', provider_info.get('cluster').get('max_nodes'), params.get('provider'))
    ctx.config.set('cluster/type', provider_info.get('cluster').get('type'), params.get('provider'))

    evaluation_options = experiment_session.get('model_settings', {}).get('evaluation_options')

    ctx.config.set('model_type', 
        "classification" if evaluation_options.get('classification', True) else "regression")
    #TODO: get target, exclude etc from dataset_statistics see _fill_data_options
    ctx.config.set('target', evaluation_options.get('targetFeature'))

    ctx.config.set('experiment/cross_validation_folds', 
        evaluation_options.get('crossValidationFolds', 5))
    ctx.config.set('experiment/max_total_time', 
        evaluation_options.get('max_total_time_mins', 60))
    ctx.config.set('experiment/max_eval_time', 
        evaluation_options.get('max_eval_time_mins', 6))
    ctx.config.set('experiment/max_n_trials', 
        evaluation_options.get('max_n_trials', 100))
    ctx.config.set('experiment/use_ensemble', 
        evaluation_options.get('use_ensemble', True))
    ctx.config.set('experiment/metric', 'accuracy')
        #evaluation_options.get('scoring', 6), params.get('provider'))

    ctx.config.clean_changes()    
    res = A2ML(ctx).train()

    print(ctx.config.parts_changes.keys())
    return res
        # options = {
        #     'crossValidationFolds':
        #         config.get('experiment/cross_validation_folds', 5),
        #     'max_total_time_mins':
        #         config.get('experiment/max_total_time', 60),
        #     'max_eval_time_mins':
        #         config.get('experiment/max_eval_time', 6),
        #     'max_n_trials':
        #         config.get('experiment/max_n_trials', 1000),
        #     'use_ensemble':
        #         config.get('experiment/use_ensemble', True),
        #     'classification':
        #         True if model_type == 'classification' else False,
        #     'scoring':
        #         config.get('experiment/metric',
        #             'f1_macro' if model_type == 'classification' else 'r2'),
        #     'test_data_path': test_data_path
        # }

        # experiment_session = AugerMessenger(params).get_experiment_session(
        #     params['augerInfo']['experiment_session_id'])

        # if 'model_settings' in experiment_session:
        #     auger_info = copy.deepcopy(params['augerInfo'])
        #     params.update(experiment_session['model_settings'].get(
        #         'evaluation_options', {}))
        #     params['dataset_statistics'] = experiment_session.get('dataset_statistics', {})

        #     # ['dataset_manifest_id'] = experiment_session['dataset_manifest_id']
        #     params['augerInfo'].update(auger_info)
        #     logging.info("evaluate_start_task augerInfo: %s"%params['augerInfo'])

    # FSClient().waitForFSReady()
    # params = AugerML.update_task_params(params, create_project_run=False)
    # #params['evaluate_task_id'] = evaluate_task_id

    # aml = AugerML(params)
    # aml.update_options_by_project_settings()
    # return aml.evaluate_start(run_top_pipelines=True,
    #                           clean_project_runs=params.get('clean_project_runs', False))

@celeryApp.task(ignore_result=False, after_return=process_task_result)
def score_actuals_by_model_task(params):
    return ModelReview(params).score_actuals(
        actuals_path = params.get('actuals_path'),
        actual_records=params.get('actual_records'),
        prediction_group_id=params.get('prediction_group_id', None),
        primary_prediction_group_id=params.get('primary_prediction_group_id', None),
        primary_model_path=ModelHelper.get_model_path(params.get('primary_pipeline_id', None),
            params.get('augerInfo', {}).get('projectPath')),
        actual_date=params.get('actual_date'),
        actuals_id=params.get('actuals_id')
    )

@celeryApp.task(ignore_result=False, after_return=process_task_result)
def count_actuals_by_prediction_id_task(params):
    return ModelReview(params).count_actuals_by_prediction_id()

@celeryApp.task(ignore_result=False, after_return=process_task_result)
def score_model_performance_daily_task(params):
    return ModelReview(params).score_model_performance_daily(
        date_from=params.get('date_from'),
        date_to=params.get('date_to')
    )

@celeryApp.task(ignore_result=False, after_return=process_task_result)
def set_support_review_model_flag_task(params):
    return ModelReview(params).set_support_review_model_flag(
        flag_value=params.get('support_review_model')
    )

@celeryApp.task(ignore_result=False, after_return=process_task_result)
def remove_model_task(params):
    return ModelReview(params).remove_model()

@celeryApp.task(ignore_result=False, after_return=process_task_result)
def distribution_chart_stats_task(params):
    return ModelReview(params).distribution_chart_stats(
        date_from=params.get('date_from'),
        date_to=params.get('date_to')
    )

@celeryApp.task(ignore_result=False, after_return=process_task_result)
def clear_model_results_and_actuals(params):
    return ModelReview(params).clear_model_results_and_actuals()

@celeryApp.task(ignore_result=False, after_return=process_task_result)
def build_review_data_task(params):
    return ModelReview(params).build_review_data(
        data_path=params.get('data_path')
    )
