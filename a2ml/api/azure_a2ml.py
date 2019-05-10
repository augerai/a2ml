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

# check core SDK version number
print("Azure ML SDK Version: ", azureml.core.VERSION)
try:  # get the preloaded workspace definition
    ws = Workspace.from_config()
except:  # or create a new one
    ws = Workspace.create(name='autoautoml_ws',
                        subscription_id='d1b17dd2-ba8a-4492-9b5b-10c6418420ce',	
                        resource_group='autoautoml_resources',
                        create_resource_group=True,
                        location='eastus2' 
                        )
    ws.write_config()

# choose a name for your cluster
compute_name = os.environ.get("AML_COMPUTE_CLUSTER_NAME", "cpucluster")
compute_min_nodes = os.environ.get("AML_COMPUTE_CLUSTER_MIN_NODES", 0)
compute_max_nodes = os.environ.get("AML_COMPUTE_CLUSTER_MAX_NODES", 4)

# This example uses CPU VM. For using GPU VM, set SKU to STANDARD_NC6
vm_size = os.environ.get("AML_COMPUTE_CLUSTER_SKU", "STANDARD_D2_V2")


if compute_name in ws.compute_targets:
    compute_target = ws.compute_targets[compute_name]
    if compute_target and type(compute_target) is AmlCompute:
        print('found compute target. just use it. ' + compute_name)
else:
    print('creating a new compute target...')
    provisioning_config = AmlCompute.provisioning_configuration(vm_size = vm_size,
                                                                min_nodes = compute_min_nodes, 
                                                                max_nodes = compute_max_nodes)

    # create the cluster
    compute_target = ComputeTarget.create(ws, compute_name, provisioning_config)
    
    # can poll for a minimum number of nodes and for a specific timeout. 
    # if no min node count is provided it will use the scale settings for the cluster
    compute_target.wait_for_completion(show_output=True, min_node_count=None, timeout_in_minutes=20)
    
     # For a more detailed view of current AmlCompute status, use get_status()
    print(compute_target.get_status().serialize())

experiment_name = "heart" # a default experiment if no argument
experiment_name = os.sys.argv[1]
print("Experiment: "+experiment_name)
exp = Experiment(workspace=ws, name=experiment_name)

project_folder = './project'

output = {}
output['SDK version'] = azureml.core.VERSION
output['Subscription ID'] = ws.subscription_id
output['Workspace'] = ws.name
output['Resource Group'] = ws.resource_group
output['Location'] = ws.location
output['Project Directory'] = project_folder
pd.set_option('display.max_colwidth', -1)
pd.DataFrame(data=output, index=['']).T

# get_data script does this now
csv_file = experiment_name + ".csv" 

automl_settings = {
    "iteration_timeout_minutes" : 10,
    "iterations" : 30,
    "primary_metric" : 'spearman_correlation',
    "preprocess" : True,
    "verbosity" : logging.DEBUG,
    "n_cross_validations": 5
}
dflow = dprep.read_csv

automl_config = AutoMLConfig(task='regression',
                             debug_log='automl_errors.log',
                             path=project_folder,
                             compute_target = compute_target,
                             data_script= "get_data.py",
                             **automl_settings
                            )


experiment=Experiment(ws, 'automl_remote')
remote_run = experiment.submit(automl_config, show_output=True)