import os

from .mparts.deploy import ModelDeploy
from .mparts.predict import ModelPredict
from .mparts.actual import ModelActual
from a2ml.api.model_review.model_review import ModelReview


class Model(object):
    """Auger Cloud Model(s) management."""

    def __init__(self, ctx, project):
        super(Model, self).__init__()
        self.project = project
        self.ctx = ctx

    def deploy(self, model_id, locally=False, review=True):
        return ModelDeploy(self.ctx, self.project).execute(model_id, locally, review)

    def predict(self, filename, model_id, threshold=None, locally=False, data=None, columns=None, output=None):
        if locally:
            self.deploy(model_id, locally)
            
        return ModelPredict(self.ctx).execute(filename, model_id, threshold, locally, data, columns, output)

    def actual(self, filename, model_id, locally):
        if locally:
            is_loaded, model_path, model_name = ModelDeploy(self.ctx, self.project).\
                verify_local_model(model_id)

            if not is_loaded:
                raise AugerException('Model should be deployed locally.')

            model_path, model_existed = ModelPredict(self.ctx)._extract_model(model_name)
            return ModelReview({'model_path': os.path.join(model_path, "model")}).score_actuals(
              actuals_path=filename, actual_records=None, actual_date=None
            )
        else:    
            return ModelActual(self.ctx).execute(filename, model_id, locally)
