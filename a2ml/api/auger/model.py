from .impl.cloud.rest_api import RestApi
from .impl.decorators import error_handler, authenticated, with_project
from .impl.model import Model
from .credentials import Credentials

class AugerModel(object):

    def __init__(self, ctx):
        self.ctx = ctx
        credentials = Credentials(ctx).load()
        self.ctx.rest_api = RestApi(
            credentials.api_url, credentials.token)

    @error_handler
    @authenticated
    @with_project(autocreate=False)
    def deploy(self, project, model_id, locally):
        model_id = Model(self.ctx, project).deploy(model_id, locally)
        return {'model_id': model_id}

    @error_handler
    @authenticated
    @with_project(autocreate=False)
    def predict(self, project, filename, model_id, threshold, locally, data, columns):
        predicted = Model(self.ctx, project).predict(
            filename, model_id, threshold, locally, data, columns)
        return {'predicted': predicted}

    @error_handler
    @authenticated
    @with_project(autocreate=False)
    def actual(self, project, filename, model_id):
        Model(self.ctx, project).actual(
            filename, model_id)
        return ''
