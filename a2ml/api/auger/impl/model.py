import os

from .mparts.deploy import ModelDeploy
from .mparts.undeploy import ModelUndeploy
from .mparts.predict import ModelPredict
from .mparts.actual import ModelActual
from .mparts.delete_actual import ModelDeleteActual
from a2ml.api.model_review.model_review import ModelReview
from .exceptions import AugerException
from .cloud.endpoint import AugerEndpointApi
from .cloud.pipeline import AugerPipelineApi

class Model(object):
    """Auger Cloud Model(s) management."""

    def __init__(self, ctx, project):
        super(Model, self).__init__()
        self.project = project
        self.ctx = ctx

    def deploy(self, model_id, locally=False, review=True, name=None, algorithm=None, score=None):
        return ModelDeploy(self.ctx, self.project).execute(model_id, locally, review, name, algorithm, score)

    def review_alert(self, model_id, parameters):
        return ModelDeploy(self.ctx, self.project).create_update_review_alert(model_id, None, parameters)

    def review(self, model_id):
        return ModelDeploy(self.ctx, self.project).review(model_id)

    def undeploy(self, model_id, locally=False):
        return ModelUndeploy(self.ctx, self.project).execute(model_id, locally)

    def predict(self, filename, model_id, threshold=None, locally=False, data=None, columns=None, predicted_at=None, output=None):
        if locally:
            self.deploy(model_id, locally)

        return ModelPredict(self.ctx).execute(filename, model_id, threshold, locally, data, columns, predicted_at, output)

    def actuals(self, model_id, filename=None, data=None, columns=None, actuals_at=None, actual_date_column=None, locally=False):
        if locally:
            is_loaded, model_path, model_name = ModelDeploy(self.ctx, self.project).\
                verify_local_model(model_id)

            if not is_loaded:
                raise AugerException('Model should be deployed locally.')

            model_path, model_existed = ModelPredict(self.ctx)._extract_model(model_name)
            params = {
                'model_path': os.path.join(model_path, "model"),
                'roi': {
                    'filter': str(self.ctx.config.get('review/roi/filter')),
                    'revenue': str(self.ctx.config.get('review/roi/revenue')),
                    'investment': str(self.ctx.config.get('review/roi/investment')),
                }
            }
            return ModelReview(params).add_actuals(
              self.ctx,
              actuals_path=filename,
              data=data,
              columns=columns,
              actual_date=actuals_at,
              actual_date_column=actual_date_column,
              provider='auger'
            )
        else:
            return ModelActual(self.ctx).execute(model_id, filename, data, columns, actuals_at, actual_date_column)

    def delete_actuals(self, model_id, with_predictions=False, begin_date=None, end_date=None, locally=False):
        if locally:
            is_loaded, model_path, model_name = ModelDeploy(self.ctx, self.project).\
                verify_local_model(model_id)

            if not is_loaded:
                raise AugerException('Model should be deployed locally.')

            model_path, model_existed = ModelPredict(self.ctx)._extract_model(model_name)
            return ModelReview({'model_path': os.path.join(model_path, "model")}).delete_actuals(
              with_predictions=with_predictions, begin_date=begin_date, end_date=end_date)
        else:
            return ModelDeleteActual(self.ctx).execute(model_id, with_predictions, begin_date, end_date)

    def build_review_data(self, model_id, locally, output):
        if locally:
            is_loaded, model_path, model_name = ModelDeploy(self.ctx, self.project).\
                verify_local_model(model_id)

            if not is_loaded:
                raise AugerException('Model should be deployed locally.')

            model_path, model_existed = ModelPredict(self.ctx)._extract_model(model_name)
            return ModelReview({'model_path': os.path.join(model_path, "model")}).build_review_data(
              data_path=self.ctx.config.get("source"), output=output)
        else:
            raise Exception("Not Implemented.")
