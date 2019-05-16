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

class AZModel(a2ml.Model):  

    def __init__(self,name,project_id,compute_region,compute_name):
        self.name = name
        self.project_id = project_id
        if compute_region is None:
            compute_region = 'eastus2'
        self.compute_region = compute_region
        # check core SDK version number
        print("Azure ML SDK Version: ", azureml.core.VERSION)
        subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
        try:  # get the preloaded workspace definition
            self.ws = Workspace.from_config(path='.azure/config.json')
        except:  # or create a new one

            resource_group = project_id + '_resources'
            self.ws = Workspace.create(name=project_id,
                        subscription_id=subscription_id,	
                        resource_group=resource_group,
                        create_resource_group=True,
                        location=compute_region 
                        )


        self.ws.write_config() 
        # choose a name for your cluster
        self.compute_name = compute_name
        self.min_nodes =  0
        self.max_nodes = 4
        # This example uses CPU VM. For using GPU VM, set SKU to STANDARD_NC6
        self.vm_size = os.environ.get("AML_COMPUTE_CLUSTER_SKU", "STANDARD_D2_V2")

        if self.compute_name in self.ws.compute_targets:
            compute_target = self.ws.compute_targets[compute_name]
            if compute_target and type(compute_target) is AmlCompute:
                print('found compute target. just use it. ' + compute_name)
        else: 
            print('Creating new AML compute context.')
            provisioning_config = AmlCompute.provisioning_configuration(vm_size=self.vm_size, min_nodes=self.min_nodes, max_nodes=self.max_nodes)
            compute_target = ComputeTarget.create(self.ws, self.compute_name, provisioning_config)
            compute_target.wait_for_completion(show_output = True)

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
        template = open("a2ml/api/get_data.template","r")
        text = template.read()
        template.close 
        print("Replacing $SOURCE with: {}".format(self.source))
        text=text.replace("SOURCE",self.source)
        text=text.replace("TARGET",self.target)
        print("Generated data script contents: {}".format(text))
        script = open(self.data_script,"w")
        script.write(text)
        script.close

    def train(self,source,target,excluded,budget,metric):

        if (metric is None):
            metric = 'spearman_correlation'
        self.target = target
        self.source = source
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
