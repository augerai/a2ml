from .celery_app import celeryApp
import logging
import copy
import os
import json
import jsonpickle

from a2ml.api.utils.context import Context
from a2ml.api.a2ml import A2ML
from a2ml.api.a2ml_dataset import A2MLDataset
from a2ml.api.a2ml_experiment import A2MLExperiment
from a2ml.api.a2ml_model import A2MLModel
from a2ml.api.a2ml_project import A2MLProject
from a2ml.server.notification import SyncSender

notificator = SyncSender()

def create_context(params, new_project=False):
    if params.get('context'):
        ctx = jsonpickle.decode(params['context'])

        ctx.set_runs_on_server(True)
        ctx.config.set('config', 'use_server', False)
        ctx.notificator = notificator
        ctx.request_id = params['_request_id']
        ctx.setup_logger(format='')
    else:
        # For Tasks Test Only!
        project_path = os.path.join(
            os.environ.get('A2ML_PROJECT_PATH', ''), params.get('project_name')
        )

        ctx = Context(path=project_path, debug = params.get("debug_log", False))

        if not new_project:
            if params.get("provider"):
                ctx.config.set('config', 'providers', [params.get("provider")])

            if params.get("source_path"):
                ctx.config.set('config', 'source', params.get("source_path"))


    tmp_dir = os.path.join(os.path.dirname(__file__), 'tmp')

    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    # For Azure, since it package current directory
    os.chdir(tmp_dir)

    return ctx

def __handle_task_result(self, status, retval, task_id, args, kwargs, einfo):
    request_id = args[0]['_request_id']

    if status == 'SUCCESS':
        notificator.publish_result(request_id, status, retval)
    else:
        notificator.publish_result(
            request_id,
            status,
            __error_to_result(retval, einfo)
        )

def execute_tasks(tasks_func, params):
    if os.environ.get('TEST_CALL_CELERY_TASKS'):
        return tasks_func(params)
    else:
        ar = tasks_func.delay(params)
        return ar.get()

# Projects
@celeryApp.task(after_return=__handle_task_result)
def new_project_task(params):
    return with_context(
        params,
        lambda ctx: A2MLProject(ctx, None).create(*params['args'], **params['kwargs'])
    )

@celeryApp.task(after_return=__handle_task_result)
def list_projects_task(params):
    def func(ctx):
        res = A2MLProject(ctx, None).list(*params['args'], **params['kwargs'])
        return __map_collection_to_name(res, 'projects')

    return with_context(params, func)

@celeryApp.task(after_return=__handle_task_result)
def delete_project_task(params):
    return with_context(
        params,
        lambda ctx: A2MLProject(ctx, None).delete(*params['args'], **params['kwargs'])
    )

@celeryApp.task(after_return=__handle_task_result)
def select_project_task(params):
    return with_context(
        params,
        lambda ctx: A2MLProject(ctx, None).select(*params['args'], **params['kwargs'])
    )

# Datasets
@celeryApp.task(after_return=__handle_task_result)
def new_dataset_task(params):
    return with_context(
        params,
        lambda ctx: A2MLDataset(ctx, None).create(*params['args'], **params['kwargs'])
    )

@celeryApp.task(after_return=__handle_task_result)
def list_datasets_task(params):
    def func(ctx):
        res = A2MLDataset(ctx, None).list(*params['args'], **params['kwargs'])
        return __map_collection_to_name(res, 'datasets')

    return with_context(params, func)

@celeryApp.task(after_return=__handle_task_result)
def delete_dataset_task(params):
    return with_context(
        params,
        lambda ctx: A2MLDataset(ctx, None).delete(*params['args'], **params['kwargs'])
    )

@celeryApp.task(after_return=__handle_task_result)
def select_dataset_task(params):
    return with_context(
        params,
        lambda ctx: A2MLDataset(ctx, None).select(*params['args'], **params['kwargs'])
    )

# Experiment
@celeryApp.task(after_return=__handle_task_result)
def list_experiments_task(params):
    def func(ctx):
        res = A2MLExperiment(ctx, None).list(*params['args'], **params['kwargs'])
        return __map_collection_to_name(res, 'experiments')

    return with_context(params, func)

@celeryApp.task(after_return=__handle_task_result)
def leaderboard_experiment_task(params):
    return with_context(
        params,
        lambda ctx: A2MLExperiment(ctx, None).leaderboard(*params['args'], **params['kwargs'])
    )

@celeryApp.task(after_return=__handle_task_result)
def history_experiment_task(params):
    return with_context(
        params,
        lambda ctx: A2MLExperiment(ctx, None).history(*params['args'], **params['kwargs'])
    )

@celeryApp.task(after_return=__handle_task_result)
def start_experiment_task(params):
    return with_context(
        params,
        lambda ctx: A2MLExperiment(ctx, None).start(*params['args'], **params['kwargs'])
    )

@celeryApp.task(after_return=__handle_task_result)
def stop_experiment_task(params):
    return with_context(
        params,
        lambda ctx: A2MLExperiment(ctx, None).stop(*params['args'], **params['kwargs'])
    )

# Models
@celeryApp.task(after_return=__handle_task_result)
def actual_model_task(params):
    return with_context(
        params,
        lambda ctx: A2MLModel(ctx, None).actual(*params['args'], **params['kwargs'])
    )

@celeryApp.task(after_return=__handle_task_result)
def deploy_model_task(params):
    return with_context(
        params,
        lambda ctx: A2MLModel(ctx, None).deploy(*params['args'], **params['kwargs'])
    )

@celeryApp.task(after_return=__handle_task_result)
def predict_model_task(params):
    return with_context(
        params,
        lambda ctx: A2MLModel(ctx, None).predict(*params['args'], **params['kwargs'])
    )

# Complex tasks
@celeryApp.task(after_return=__handle_task_result)
def import_data_task(params):
    return with_context(
        params,
        lambda ctx: A2ML(ctx).import_data(*params['args'], **params['kwargs'])
    )

@celeryApp.task(after_return=__handle_task_result)
def train_task(params):
    return with_context(
        params,
        lambda ctx: A2ML(ctx).train(*params['args'], **params['kwargs'])
    )

@celeryApp.task(after_return=__handle_task_result)
def evaluate_task(params):
    return with_context(
        params,
        lambda ctx: A2ML(ctx).evaluate(*params['args'], **params['kwargs'])
    )

@celeryApp.task(after_return=__handle_task_result)
def deploy_task(params):
    return with_context(
        params,
        lambda ctx: A2ML(ctx).deploy(*params['args'], **params['kwargs'])
    )

@celeryApp.task(after_return=__handle_task_result)
def predict_task(params):
    return with_context(
        params,
        lambda ctx: A2ML(ctx).predict(*params['args'], **params['kwargs'])
    )

@celeryApp.task(after_return=__handle_task_result)
def review_task(params):
    # TODO
    raise Exception('not inplemented yet')

@celeryApp.task(after_return=__handle_task_result)
def demo_task(params):
    import time
    request_id = params['_request_id']
    for i in range(0, 10):
        notificator.publish_log(request_id, 'info', 'log ' + str(i))
        time.sleep(2)

    notificator.publish_result(request_id, 'SUCCESS', 'done')

def with_context(params, proc):
    ctx = create_context(params)

    if not 'args' in params:
        params['args'] = []

    if not 'kwargs' in params:
        params['kwargs'] = {}

    res = proc(ctx)

    ctx.set_runs_on_server(False)
    ctx.config.set('config', 'use_server', True)
    return {'response': res, 'config': jsonpickle.encode(ctx.config)}

def __exception_message_with_all_causes(e):
    if isinstance(e, Exception) and e.__cause__:
        return str(e) + ' caused by ' + __exception_message_with_all_causes(e.__cause__)
    else:
        return str(e)

def __error_to_result(retval, einfo):
    res = __exception_message_with_all_causes(retval)

    if einfo:
        res += '\n' + str(einfo)

    return res

def __map_collection_to_name(res, collection_name):
    for provder in res.keys():
        if collection_name in res[provder]['data']:
            res[provder]['data'][collection_name] = list(
                map(lambda x: x.get('name'), res[provder]['data'][collection_name])
            )
