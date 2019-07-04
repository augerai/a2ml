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
        print("Azure ML SDK Version: {}".format(azureml.core.VERSION))
        print("Current directory: {}".format(os.getcwd()))
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
                print('Found compute target. Just use it: ' + self.compute_cluster)
        else: 
            print('Creating new AML compute context.')
            provisioning_config = AmlCompute.provisioning_configuration(vm_size=self.compute_sku, min_nodes=self.compute_min_nodes, max_nodes=self.compute_max_nodes)
            compute_target = ComputeTarget.create(self.ws, self.compute_cluster, provisioning_config)
            compute_target.wait_for_completion(show_output = True)

    def upload_file(self,source_file):
        print("Copying {} to {}".format(self.source,self.file_share))
        cmd = "az storage file upload --source " + self.source 
        cmd = cmd +  " --share-name " + self.file_share
        cmd = cmd + " --account-name " + self.account_name + " --account-key " + self.account_key
        print("Running command: {}".format(cmd))
        result = os.system(cmd)
        print("Result of local copy to Azure file share: {}".format(result)) 
    
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
        print("Current working directory: {}".format(os.getcwd()))
        template = open("get_data.template","r")
        text = template.read()
        template.close 
        print("Replacing $SOURCE with: {}".format(self.data_file))
        text=text.replace("$SOURCE",self.data_file)
        text=text.replace("$TARGET",self.target)
        print("Generated data script contents: {}".format(text))
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
        print("Submitting training run: {}:".format(self.ws))
        remote_run = experiment.submit(self.automl_config, show_output=True)
        print("Results of training run: {}:".format(remote_run))

    def evaluate(self):
        pass
    def deploy(self):
        pass
    def predict(self,filepath,score_threshold):
        pass
    def review(self):
        pass
