from .impl.cloud.rest_api import RestApi
from .impl.decorators import error_handler, authenticated, with_project
from .impl.model import Model
from .credentials import Credentials

class AugerModel(object):

    def __init__(self, ctx):
        self.ctx = ctx
        self.ctx.credentials = Credentials(ctx).load()
        self.ctx.rest_api = RestApi(
            self.ctx.credentials.api_url, self.ctx.credentials.token)

    @error_handler
    @authenticated
    @with_project(autocreate=False)
    def deploy(self, project, model_id, locally):
        model_id = Model(self.ctx, project).deploy(model_id, locally)
        return {'model_id': model_id}

    @error_handler
    @authenticated
    @with_project(autocreate=False)
    def predict(self, project, filename, model_id, threshold, locally):
        predicted = Model(self.ctx, project).predict(
            filename, model_id, threshold, locally)
        return {'predicted': predicted}

    @error_handler
    @authenticated
    @with_project(autocreate=False)
    def actual(self, project, filename, model_id):
        Model(self.ctx, project).actual(
            filename, model_id)
        return ''
