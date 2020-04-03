from .celery_app import celeryApp
import logging
import copy
import os
import json
import jsonpickle

from a2ml.api.utils.context import Context
from auger.api.cloud.rest_api import RestApi
from a2ml.api.a2ml import A2ML
from a2ml.api.a2ml_project import A2MLProject
from a2ml.server.notification import SyncSender

notificator = SyncSender()

def create_context(params, new_project=False):
    if params['context']:
        ctx = jsonpickle.decode(params['context'])
    else:
        # TODO:path to config files
        project_path = os.path.join(
            os.environ.get('A2ML_PROJECT_PATH', ''), params.get('project_name')
        )

        os.chdir("tmp")
        print(os.getcwd())
        ctx = Context(path=project_path, debug = params.get("debug_log", False))

        if not new_project:
            if params.get("provider"):
                ctx.config.set('config', 'providers', [params.get("provider")])

            if params.get("source_path"):
                ctx.config.set('config', 'source', params.get("source_path"))

        if os.environ.get('AUGER_PROJECT_API_TOKEN'):
            os.environ['AUGER_CREDENTIALS'] = json.dumps({
                'organization' : os.environ.get('AUGER_ORGANIZATION'),
                'url' : os.environ.get('HUB_APP_URL'),
                'token' : os.environ.get('AUGER_PROJECT_API_TOKEN')
            })

        if os.environ.get('AZURE_SUBSCRIPTION_ID'):
            ctx.config.set('azure', 'subscription_id', os.environ.get('AZURE_SUBSCRIPTION_ID'))

        if os.environ.get('AZURE_SERVICE_PRINCIPAL_TENANT_ID'):
            os.environ['AZURE_CREDENTIALS'] = json.dumps({
                'service_principal_tenant_id' : os.environ.get('AZURE_SERVICE_PRINCIPAL_TENANT_ID'),
                'service_principal_id' : os.environ.get('AZURE_SERVICE_PRINCIPAL_ID'),
                'service_principal_password' : os.environ.get('AZURE_SERVICE_PRINCIPAL_PASSWORD')
            })

    ctx.runs_on_server = True
    ctx.notificator = notificator
    ctx.request_id = params['_request_id']
    ctx.config.set('config', 'use_server', False)
    ctx.setup_logger(format='')

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

def execute_tasks(tasks_func, params):
    if os.environ.get('TEST_CALL_CELERY_TASKS'):
        return tasks_func(params)
    else:
        ar = tasks_func.delay(params)
        return ar.get()

@celeryApp.task()
def new_project_task(params):
    from a2ml.cmdl.commands.cmd_new import NewCmd

    ctx = create_context(params, new_project = True)

    NewCmd(ctx, params.get('project_name'), params.get('providers'),
        params.get('target'), params.get("source_path"),
        params.get("model_type")).create_project()

@celeryApp.task(after_return=__handle_task_result)
def list_projects_task(params):
    ctx = create_context(params)
    res = A2MLProject(ctx, None).list()

    for provder in res.keys():
        res[provder]['data']['projects'] = list(
            map(lambda x: x.get('name'), res[provder]['data']['projects'])
        )

    return  res

@celeryApp.task()
def import_data_task(params):
    ctx = create_context(params)

    return A2ML(ctx).import_data()

@celeryApp.task()
def train_task(params):
    ctx = create_context(params)

    return A2ML(ctx).train()

@celeryApp.task()
def evaluate_task(params):
    ctx = create_context(params)

    return A2ML(ctx).evaluate()

@celeryApp.task()
def deploy_task(params):
    ctx = create_context(params)

    return A2ML(ctx).deploy(params.get('model_id'))

@celeryApp.task()
def predict_task(params):
    ctx = create_context(params)

    return A2ML(ctx).predict(
        params.get('filename'),
        params.get('model_id'),
        params.get('threshold'))
