import lightgbm as lgb
import numpy as np
import pandas as pd
import os
import logging
import azureml.core 
from azureml.core import Workspace
from azureml.core import Experiment
from azureml.core.compute import AmlCompute
from azureml.core.compute import ComputeTarget
from sklearn.model_selection import train_test_split
from azureml.train.automl import AutoMLConfig
from azureml.core.experiment import Experiment
import azureml.dataprep as dprep

from a2ml.api import a2ml
class AzureA2ML(object):  
    def __init__(self,ctx):
        self.ctx = ctx
        self.name = ctx.config['config'].get('name',None)
        self.source = ctx.config['config'].get('source', None)
        self.target = ctx.config['config'].get('target',None)
        self.exclude = ctx.config['config'].get('exclude',None)

        # global experiment settings
        # experiment: 
        #   cross_validation_folds: 5
        #   max_total_time: 60
        #   max_eval_time: 1
        #   max_n_trials: 10
        #   use_ensemble: true
        # per provider experiment settings
        self.metric = ctx.config['azure'].get('experiment/metric','spearman_correlation')
        self.cross_validation_folds = ctx.config['azure'].get('experiment/cross_validation_folds',5)
        self.max_total_time = ctx.config['config'].get('experiment/max_total_time',60)
        self.iteration_timeout_minutes = ctx.config['config'].get('experiment/iteration_timeout_minutes',10)
        self.max_n_trials = ctx.config['config'].get('experiment/max_n_trials',10)
        self.use_ensemble = ctx.config['config'].get('experiment/use_ensemble',False)
        # per provider compute settings
        self.subscription_id = ctx.config['azure'].get('subscription_id',os.environ.get("AZURE_SUBSCRIPTION_ID"))
        self.workspace = ctx.config['azure'].get('workspace',self.name+'_ws')
        self.resource_group = ctx.config['azure'].get('resource_group',self.name+'_resources')
        # cluster specific options
        self.compute_cluster = ctx.config['azure'].get('cluster/name','cpucluster')
        self.compute_region = ctx.config['azure'].get('cluster/region','eastus2')
        self.compute_min_nodes = ctx.config['azure'].get('cluster/min_nodes',0)
        self.compute_max_nodes = ctx.config['azure'].get('cluster/max_nodes',4)
        self.compute_sku = ctx.config['azure'].get('cluster/type','STANDARD_D2_V2')
        # azure-specific file-related options
        self.file_share = ctx.config['azure'].get('file_share',None)
        self.account_name = ctx.config['azure'].get('account_name',None)
        self.account_key = ctx.config['azure'].get('account_key',None)  
        # example: https://autoautostorage68c87c828.file.core.windows.net/a2ml/baseball.csv
        default_data_file = "https://" + self.account_name + ".file.core.windows.net/" + self.file_share + "/" + os.path.basename(self.source)
        self.data_file = ctx.config['azure'].get('file_share',default_data_file)         

        # check core SDK version number
        self.ctx.log("Azure ML SDK Version: {}".format(azureml.core.VERSION))
        self.ctx.log("Current directory: {}".format(os.getcwd()))
        try:  # get the preloaded workspace definition
            self.ws = Workspace.from_config(path='./.azureml/config.json')
        except:  # or create a new one
            self.ws = Workspace.create(name=self.workspace,
                        subscription_id=self.subscription_id,	
                        resource_group=self.resource_group,
                        create_resource_group=True,
                        location=self.compute_region)
        self.ws.write_config() 
        if self.compute_cluster in self.ws.compute_targets:
            compute_target = self.ws.compute_targets[self.compute_cluster]
            if compute_target and type(compute_target) is AmlCompute:
                self.ctx.log('Found compute target. Just use it: ' + self.compute_cluster)
        else: 
            self.ctx.log('Creating new AML compute context.')
            provisioning_config = AmlCompute.provisioning_configuration(vm_size=self.compute_sku, min_nodes=self.compute_min_nodes, max_nodes=self.compute_max_nodes)
            compute_target = ComputeTarget.create(self.ws, self.compute_cluster, provisioning_config)
            compute_target.wait_for_completion(show_output = True)

    def upload_file(self,source_file):
        self.ctx.log("Copying {} to {}".format(self.source,self.file_share))
        cmd = "az storage file upload --source " + self.source 
        cmd = cmd +  " --share-name " + self.file_share
        cmd = cmd + " --account-name " + self.account_name + " --account-key " + self.account_key
        self.ctx.log("Running command: {}".format(cmd))
        result = os.system(cmd)
        self.ctx.log("Result of local copy to Azure file share: {}".format(result)) 
    
    def import_data(self):
        self.exp = Experiment(workspace=self.ws, name=self.name)
        self.project_folder = './project'
        output = {}
        output['SDK version'] = azureml.core.VERSION
        output['Subscription ID'] = self.ws.subscription_id
        output['Workspace'] = self.ws.name
        output['Resource Group'] = self.ws.resource_group
        output['Location'] = self.ws.location
        output['Project Directory'] = self.project_folder
        pd.set_option('display.max_colwidth', -1)
        pd.DataFrame(data=output, index=['']).T
        self.upload_file(self.source)

    def generate_data_script(self):
        self.ctx.log("Current working directory: {}".format(os.getcwd()))
        template = open("get_data.template","r")
        text = template.read()
        template.close 
        self.ctx.log("Replacing $SOURCE with: {}".format(self.data_file))
        text=text.replace("$SOURCE",self.data_file)
        text=text.replace("$TARGET",self.target)
        self.ctx.log("Generated data script contents: {}".format(text))
        script = open(self.data_script,"w")
        script.write(text)
        script.close

    def train(self):   
        automl_settings = {
            "iteration_timeout_minutes" : self.iteration_timeout_minutes,
            "iterations" : self.max_n_trials,
            "primary_metric" : self.metric,
            "verbosity" : logging.DEBUG,
            "n_cross_validations": self.cross_validation_folds,
            "enable_stack_ensemble": self.use_ensemble
        }
        self.data_script = "get_data.py"
        self.generate_data_script()
        self.automl_config = AutoMLConfig(task='regression',
                                    path = os.getcwd(),
                                    debug_log='automl_errors.log',
                                    compute_target = self.compute_cluster,
                                    data_script = "./get_data.py",
                                    **automl_settings
                                    ) 
        experiment=Experiment(self.ws, 'automl_remote')
        self.ctx.log("Submitting training run: {}:".format(self.ws))
        remote_run = experiment.submit(self.automl_config, show_output=True)
        self.ctx.log("Results of training run: {}:".format(remote_run))

    def evaluate(self):
        raise NotImplementedError()
        # TODO: Adopt from Google to Azure
        credentials, project = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
        authed_session = AuthorizedSession(credentials)
        basename="https://automl.googleapis.com/v1beta1/"
        cmd = basename + self.operation_name
        response=authed_session.get(cmd)
        result=json.loads(response.content)
        self.ctx.log("Operation name: {}".format(result["name"]))
     
        if (("done" in result.keys()) and result["done"]): 
            self.ctx.log("Model training complete.")
            self.model_name = result["response"]["name"]
            self.ctx.log("Model full name: {}".format(self.model_name))   
            self.ctx.config['google'].yaml['model_name'] = self.model_name
            self.ctx.config['google'].write()  
            response = self.client.list_model_evaluations(self.model_name)
            self.ctx.log("List of model evaluations:")
            for evaluation in response:
                self.ctx.log("Model evaluation name: {}".format(evaluation.name))
                self.ctx.log("Model evaluation id: {}".format(evaluation.name.split("/")[-1]))
                self.ctx.log("Model evaluation example count: {}".format(
                    evaluation.evaluated_example_count))
                self.ctx.log("Model evaluation time: {} seconds".format(evaluation.create_time.seconds))
                self.ctx.log("Full model evaluation: {}".format(inspect.getmembers(evaluation) ))
                self.ctx.log("\n")

    def deploy(self,  model_id, locally=False):
        raise NotImplementedError()
        # TODO: Adopt from Google to Azure
        self.ctx.log('Azure Deploy'.format(model_id))
        if (model_id is None):
            model_name = self.model_name
        else:
            model_name = self.client.model_path(self.project_id, self.compute_region, self.id)
        try: 
            self.ctx.log('Deploy model: {}'.format(self.model_name))
            response = self.client.deploy_model(self.model_name)
            self.ctx.log("Deploy result: {}".format(response))
        except google.api_core.exceptions.FailedPrecondition as inst:
            self.ctx.log("Failed to deploy because its already deploying: {}...".format(inst))

    def predict(self,filename, model_id, threshold=None, locally=False):
        raise NotImplementedError()
        # TODO: Adopt from Google to Azure
        self.ctx.log('Azure Predict')
        prediction_client = automl.PredictionServiceClient()
        predictions_file = filename.split('.')[0]+'_predicted.csv' 
        predictions=open(predictions_file, "wt")  
        with open(filename,"rt") as csv_file:
            content = csv.reader(csv_file)
            next(reader,None)
            csvlist = ''
            for row in content:
                # Create payload
                values = []
                for column in row:
                    self.ctx.log("Column: {}".format(column))
                    values.append({'number_value': float(column)})
                csvlist=",".join(row)
                print ("CSVList: {}".format(csvlist))
                payload = {
                    'row': {'values': values}
                }
                response = prediction_client.predict(self.model_name, payload)
                self.ctx.log("Prediction results:")
                for result in response.payload:
                    if ((threshold is None) or (result.classification.score >= score_threshold)): 
                        prediction=result.tables.value.number_value
                self.ctx.log("Prediction: {}".format(prediction))
                csvlist += (',' + str(prediction) + '\n')
                predictions.write(csvlist) 
                i = i + 1

    def review(self):
        raise NotImplementedError()
        # TODO: Adopt from Google to Azure
        self.ctx.log('Azure Review')

        # Get complete detail of the model.
        model = self.client.get_model(self.model_name)

        # Retrieve deployment state.
        if model.deployment_state == enums.Model.DeploymentState.DEPLOYED:
            deployment_state = "deployed"
        else:
            deployment_state = "undeployed"

        # Display the model information.
        self.ctx.log("Model name: {}".format(self.model_name))
        self.ctx.log("Model id: {}".format(model.name.split("/")[-1]))
        self.ctx.log("Model display name: {}".format(model.display_name))
        self.ctx.log("Model metadata:")
        self.ctx.log(model.tables_model_metadata)
        self.ctx.log("Model create time (seconds): {}".format(model.create_time.seconds))
        self.ctx.log("Model deployment state: {}".format(deployment_state))
