from google.cloud import automl_v1beta1 as automl
from google.cloud.automl_v1beta1 import enums
from a2ml.cmdl.utils.config_yaml import ConfigYaml

class GoogleDeploy:
    """Deploy your Model on Google Cloud."""
    def __init__(self, ctx):
        pass

    def deploy(self, model_id, locally=False):
        self.full_id = self.client.model_path(self.project_id, self.compute_region, self.id)
        response = self.client.deploy_model(self.full_id)