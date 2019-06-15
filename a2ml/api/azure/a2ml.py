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
        self.budget = ctx.config['config'].get('budget',None)
        self.metric = ctx.config['google'].get('metric','spearman_correlation')
        self.subscription_id = ctx.config['azure'].get('subscription_id',os.environ.get("AZURE_SUBSCRIPTION_ID"))
        self.workspace = ctx.config['azure'].get('workspace',self.name+'_ws')
        self.resource_group = ctx.config['azure'].get('resource_group',self.name+'_resources')

        self.compute_region = ctx.config['azure'].get('region','eastus2')
        self.compute_cluster = ctx.config['azure'].get('compute_cluster','cpucluster')
        self.compute_min_nodes = ctx.config['azure'].get('compute_min_nodes', 0)
        self.compute_max_nodes = ctx.config['azure'].get('compute_max_nodes', 4)
        self.compute_sku = ctx.config['azure'].get('compute_sku','STANDARD_D2_V2')
 
        # check core SDK version number
        print("Azure ML SDK Version: ", azureml.core.VERSION)
        try:  # get the preloaded workspace definition
            self.ws = Workspace.from_config(path='../.azure/config.json')
        except:  # or create a new one
            self.ws = Workspace.create(name=self.workspace,
                        subscription_id=self.subscription_id,	
                        resource_group=self.resource_group,
                        create_resource_group=True,
                        location=self.compute_region 
                        )


        self.ws.write_config() 

        if self.compute_cluster in self.ws.compute_targets:
            compute_target = self.ws.compute_targets[compute_name]
            if compute_target and type(compute_target) is AmlCompute:
                print('found compute target. just use it. ' + compute_cluster)
        else: 
            print('Creating new AML compute context.')
            provisioning_config = AmlCompute.provisioning_configuration(vm_size=self.compute_sku, min_nodes=self.compute_min_nodes, max_nodes=self.compute_max_nodes)
            compute_target = ComputeTarget.create(self.workspace, self.compute_cluster, provisioning_config)
            compute_target.wait_for_completion(show_output = True)

    def import_data(self):
        self.exp = Experiment(workspace=ws, name=self.name)
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

    def generate_data_script(self):
        template = open("../a2ml/api/azure/get_data.template","r")
        text = template.read()
        template.close 
        print("Replacing $SOURCE with: {}".format(self.source))
        text=text.replace("SOURCE",self.source)
        text=text.replace("TARGET",self.target)
        print("Generated data script contents: {}".format(text))
        script = open(self.data_script,"w")
        script.write(text)
        script.close

    def train(self):

        # TODO: use metric budget specified in seconds
        automl_settings = {
            "iteration_timeout_minutes" : 10,
            "iterations" : 30,
            "primary_metric" : metric,
            "preprocess" : True,
            "verbosity" : logging.DEBUG,
            "n_cross_validations": 5
        }

        self.data_script = "get_data.py"
        self.generate_data_script()
        self.automl_config = AutoMLConfig(task='regression',
                                    debug_log='automl_errors.log',
                                    compute_target = self.target,
                                    data_script= "get_data.py",
                                    **automl_settings
                                    ) 


        experiment=Experiment(self.ws, 'automl_remote')
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
