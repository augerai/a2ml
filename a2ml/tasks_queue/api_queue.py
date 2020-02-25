import logging
import copy

from a2ml.api.utils.context import Context
from auger.api.cloud.rest_api import RestApi
from a2ml.api.a2ml import A2ML


def create_a2ml(params)
    #TODO:path to config files
    root_dir = os.environ.get('A2ML_ROOT_DIR', '')
    project_path = os.path.join(root_dir, os.environ.get('A2ML_PROJECT_PATH', ''))

    ctx = Context(path=project_path)
    ctx.rest_api = RestApi(
        os.environ.get('HUB_APP_URL'), 
        os.environ.get('AUGER_PROJECT_API_TOKEN'), 
        debug=params.get("debug_log", False))
    ctx.setup_logger(format='')

	ctx.config['config'].yaml['providers'] = [params.get("provider", 'auger')]

    return A2ML(ctx)

from .celery_app import celeryApp
@celeryApp.task()
def import_data_task(params):
    return create_a2ml(params).import_data()
