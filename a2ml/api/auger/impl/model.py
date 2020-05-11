from .mparts.deploy import ModelDeploy
from .mparts.predict import ModelPredict
from .mparts.actual import ModelActual


class Model(object):
    """Auger Cloud Model(s) management."""

    def __init__(self, ctx, project):
        super(Model, self).__init__()
        self.project = project
        self.ctx = ctx

    def deploy(self, model_id, locally=False):
        return ModelDeploy(self.ctx, self.project).execute(model_id, locally)

    def predict(self, filename, model_id, threshold=None, locally=False, data=None, columns=None):
        if locally:
            self.deploy(model_id, locally)
            
        return ModelPredict(self.ctx).execute(filename, model_id, threshold, locally, data, columns)

    def actual(self, filename, model_id):
        return ModelActual(self.ctx).execute(filename, model_id)
