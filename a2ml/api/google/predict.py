from google.cloud import automl_v1beta1 as automl
from google.cloud.automl_v1beta1 import enums
from a2ml.cmdl.utils.config_yaml import ConfigYaml

class GooglePredict:
    def __init__(self,ctx):
        self.client = automl.AutoMlClient()
        self.ctx=ctx
        self.project_id = ctx.config['google'].get('project',None)
        self.compute_region = ctx.config['google'].get('region',None)
        self.project_location = self.client.location_path(self.project_id,self.compute_region)
        self.dataset_id = ctx.config['google'].get('dataset_id',None)
        self.dataset_name = ctx.config['google'].get('dataset_name',None)
        self.source = ctx.config['google'].get('source', None)
        self.name = ctx.config['config'].get('name',None)

    def predict(self):
        pass