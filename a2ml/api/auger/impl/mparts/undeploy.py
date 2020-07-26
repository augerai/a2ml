import os

from a2ml.api.utils import fsclient
from .deploy import ModelDeploy
from ..cloud.pipeline import AugerPipelineApi


class ModelUndeploy(object):
    """Undeploy Model locally or from Auger Cloud."""

    def __init__(self, ctx, project):
        super(ModelUndeploy, self).__init__()
        self.project = project
        self.ctx = ctx

    def execute(self, model_id, locally=False):
        if locally:
            is_loaded, model_path, model_name = \
                ModelDeploy(self.ctx, self.project).verify_local_model(model_id)
            self.ctx.log("Undeploy model. Remove local model: %s" % model_name)

            if is_loaded:
                fsclient.remove_file(model_name)

            model_folder = os.path.splitext(model_name)[0]
            fsclient.remove_folder(model_folder)
        else:
            AugerPipelineApi(self.ctx, None).remove(model_id)
