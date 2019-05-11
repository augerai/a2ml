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
import dill

import a2ml

class AzModel(a2ml.api.a2ml.Model):  

    def __init__(self,name,project_id,compute_region):
        self.name = name
        self.project_id = project_id
        if compute_region is None:
            compute_region = 'eastus2'
        self.compute_region = compute_region
        # check core SDK version number
        print("Azure ML SDK Version: ", azureml.core.VERSION)

        self.subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
        try:  # get the preloaded workspace definition
            self.ws = Workspace.from_config()
        except:  # or create a new one
            resource_group = project_id + '_resources'
            self.ws = Workspace.create(name=project_id,
                        subscription_id=self.subscription_id,	
                        resource_group=resource_group,
                        create_resource_group=True,
                        location=compute_region 
                        )
        self.ws.write_config() 
        # choose a name for your cluster
        self.compute_name = os.environ.get("AML_COMPUTE_CLUSTER_NAME", "cpucluster")
        self.compute_min_nodes = os.environ.get("AML_COMPUTE_CLUSTER_MIN_NODES", 0)
        self.compute_max_nodes = os.environ.get("AML_COMPUTE_CLUSTER_MAX_NODES", 4)

        # This example uses CPU VM. For using GPU VM, set SKU to STANDARD_NC6
        self.vm_size = os.environ.get("AML_COMPUTE_CLUSTER_SKU", "STANDARD_D2_V2")

    def import_data(self,source):
        self.source = source 
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

    def generate_data_script(self):
        template = open("data_script.template","r")
        text = template.read()
        template.close 
        print("Replacing $SOURCE with: {}".format(self.source))
        text.replace("$SOURCE",self.source)
        text.replace("$TARGET",self.target)
        print("Generated data script contents: {}".format(text))
        script = open(self.data_script,"w")
        script.write(text)
        script.close

    def train(self,target,excluded,budget,metric):
        print("Loading stored model object")
 
        if (metric is None):
            metric = 'spearman_correlation'
        self.target = target
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
                                    path=self.project_folder,
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
