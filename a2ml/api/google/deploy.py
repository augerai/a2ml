from google.cloud import automl_v1beta1 as automl
from google.cloud.automl_v1beta1 import enums
from a2ml.cmdl.utils.config_yaml import ConfigYaml

class GoogleDeploy:
    """Deploy your Model on Google Cloud."""
    def __init__(self, ctx):
        self.client = automl.AutoMlClient()
        self.ctx=ctx
        self.model_name = ctx.config['google'].get('model_name',None)

    def deploy(self, model_id, locally=False):
        response = self.client.deploy_model(self.model_name)
        print("Response: {}".format(response))