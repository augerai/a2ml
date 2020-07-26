from .impl.cloud.rest_api import RestApi
from .impl.decorators import with_project
from a2ml.api.utils.decorators import error_handler, authenticated
from .impl.model import Model
from .credentials import Credentials

class AugerModel(object):

    def __init__(self, ctx):
        self.ctx = ctx
        self.credentials = Credentials(ctx).load()
        self.ctx.rest_api = RestApi(
            self.credentials.api_url, self.credentials.token)

    @error_handler
    @authenticated
    @with_project(autocreate=False)
    def deploy(self, project, model_id, locally, review):
        model_id = Model(self.ctx, project).deploy(model_id, locally, review)
        return {'model_id': model_id}

    @error_handler
    @authenticated
    @with_project(autocreate=False)
    def predict(self, project, filename, model_id, threshold, locally, data, columns, predicted_at, output):
        predicted = Model(self.ctx, project).predict(
            filename, model_id, threshold, locally, data, columns, predicted_at, output)

        if filename:
            self.ctx.log('Predictions stored in %s' % predicted)
        
        return {'predicted': predicted}

    @error_handler
    @authenticated
    @with_project(autocreate=False)
    def actuals(self, project, model_id, filename=None, actual_records=None, actuals_at=None, locally=False):
        return Model(self.ctx, project).actuals(model_id, filename, actual_records, actuals_at, locally)

    @error_handler
    @authenticated
    @with_project(autocreate=False)
    def build_review_data(self, project, model_id, locally, output):
        return Model(self.ctx, project).build_review_data(model_id, locally, output)

    @error_handler
    @authenticated
    @with_project(autocreate=False)
    def review(self, project, model_id):
        pass

    @error_handler
    @authenticated
    @with_project(autocreate=False)    
    def undeploy(self, project, model_id, locally):
        Model(self.ctx, project).undeploy(model_id, locally)
        return {'model_id': model_id}

