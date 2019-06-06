from google.cloud import automl_v1beta1 as automl
from google.cloud.automl_v1beta1 import enums
from a2ml.cmdl.utils.config_yaml import ConfigYaml
import google.auth
from google.auth.transport.requests import AuthorizedSession
import json

class GoogleEvaluate:
    """Evaluate model training from Google."""

    def __init__(self, ctx):
        self.client = automl.AutoMlClient()
        self.ctx=ctx
        self.project_id = ctx.config['google'].get('project',None)
        self.compute_region = ctx.config['google'].get('region',None)
        self.project_location = self.client.location_path(self.project_id,self.compute_region)
        self.dataset_id = ctx.config['google'].get('dataset_id',None)
        self.dataset_name = ctx.config['google'].get('dataset_name',None)
        self.source = ctx.config['google'].get('source', None)
        self.name = ctx.config['config'].get('name',None)
        self.dataset_name = self.client.dataset_path(self.project_id, self.compute_region, self.dataset_id)
        self.target = ctx.config['config'].get('target',None)
        self.exclude = ctx.config['config'].get('exclude',None)
        self.budget = ctx.config['config'].get('budget',None)
        self.metric = ctx.config['google'].get('dataset_name',None)
        if self.metric is None: 
            self.metric = "MINIMIZE_MAE"
        self.operation_name = ctx.config['google'].get('operation_name',None)
        self.model_name = ctx.config['google'].get('model_name',None)

    def evaluate(self):
        credentials, project = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
        authed_session = AuthorizedSession(credentials)
        basename="https://automl.googleapis.com/v1beta1/"
        cmd = basename + self.operation_name
        response=authed_session.get(cmd)
        print("Response content: {}".format(response.content))
        result=json.loads(response.content)
        self.model_name = result["name"]
        print("Model: {}".format(self.model_name))   
        if (("done" in result.keys()) and result["done"]): 
            self.ctx.config['google'].yaml['model_name'] = self.model_name
            self.ctx.config['google'].write()  
            response = self.client.list_model_evaluations(self.model_name)
            print("List of model evaluations:")
            for evaluation in response:
                print("Model evaluation name: {}".format(evaluation.name))
                print("Model evaluation id: {}".format(evaluation.name.split("/")[-1]))
                print("Model evaluation example count: {}".format(
                    evaluation.evaluated_example_count))
                print("Model evaluation time:")
                print("\tseconds: {}".format(evaluation.create_time.seconds))
                print("\tnanos: {}".format(evaluation.create_time.nanos))
                print("\tevaluation:{}",evaluation)
                print("\n")

