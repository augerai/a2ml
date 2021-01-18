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
    def deploy(self, project, model_id, locally, review, name, algorithm, score):
        model_id = Model(self.ctx, project).deploy(model_id, locally, review, name, algorithm, score)
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
    def actuals(self, project, model_id, filename=None, data=None, columns=None, actuals_at=None, actual_date_column=None, locally=False):
        return Model(self.ctx, project).actuals(model_id, filename, data, columns, actuals_at, actual_date_column, locally)

    @error_handler
    @authenticated
    @with_project(autocreate=False)
    def delete_actuals(self, project, model_id, with_predictions=False, begin_date=None, end_date=None, locally=False):
        return Model(self.ctx, project).delete_actuals(model_id, with_predictions, begin_date, end_date, locally)

    @error_handler
    @authenticated
    @with_project(autocreate=False)
    def review_alert(self, project, model_id, parameters):
        return Model(self.ctx, project).review_alert(model_id, parameters)

    @error_handler
    @authenticated
    @with_project(autocreate=False)
    def build_review_data(self, project, model_id, locally, output):
        return Model(self.ctx, project).build_review_data(model_id, locally, output)

    @error_handler
    @authenticated
    @with_project(autocreate=False)
    def review(self, project, model_id):
        return Model(self.ctx, project).review(model_id)

    @error_handler
    @authenticated
    @with_project(autocreate=False)
    def undeploy(self, project, model_id, locally):
        Model(self.ctx, project).undeploy(model_id, locally)
        return {'model_id': model_id}

