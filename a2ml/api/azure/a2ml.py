import os
import time
import logging
import numpy as np
import pandas as pd
import azureml.core
from azureml.core import Workspace
from azureml.core import Experiment
from azureml.core.dataset import Dataset
from azureml.core.compute import AmlCompute
from azureml.core.compute import ComputeTarget
from azureml.train.automl import AutoMLConfig
from azureml.core.experiment import Experiment
from azureml.train.automl.run import AutoMLRun

from a2ml.api import a2ml


class AzureA2ML(object):
    def __init__(self, ctx):
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
        self.model_type = ctx.config['config'].get('model_type', None)
        if (self.model_type == None):
            raise Exception('Please specify model_type')
        self.metric = ctx.config['azure'].get('experiment/metric','spearman_correlation')
        self.cross_validation_folds = ctx.config['azure'].get('experiment/cross_validation_folds',5)
        self.max_total_time = ctx.config['config'].get('experiment/max_total_time',60)
        self.iteration_timeout_minutes = ctx.config['config'].get('experiment/iteration_timeout_minutes',10)
        self.max_n_trials = ctx.config['config'].get('experiment/max_n_trials',10)
        self.use_ensemble = ctx.config['config'].get('experiment/use_ensemble',False)
        # per provider compute settings
        self.subscription_id = ctx.config['azure'].get('subscription_id',
            os.environ.get("AZURE_SUBSCRIPTION_ID"))
        self.workspace = ctx.config['azure'].get('workspace',self.name+'_ws')
        self.resource_group = ctx.config['azure'].get('resource_group',self.name+'_resources')
        # cluster specific options
        self.compute_cluster = ctx.config['azure'].get('cluster/name','cpu-cluster')
        self.compute_region = ctx.config['azure'].get('cluster/region','eastus2')
        self.compute_min_nodes = ctx.config['azure'].get('cluster/min_nodes',1)
        self.compute_max_nodes = ctx.config['azure'].get('cluster/max_nodes',4)
        self.compute_sku = ctx.config['azure'].get('cluster/type','STANDARD_D2_V2')
        # azure-specific file-related options
        self.file_share = ctx.config['azure'].get('file_share', None)
        self.account_name = ctx.config['azure'].get('account_name', None)
        self.account_key = ctx.config['azure'].get('account_key', None)
        # example: https://autoautostorage68c87c828.file.core.windows.net/a2ml/baseball.csv
        # print('account_name: ', self.account_name,
        #     'file_share: ', self.file_share, 'source: ', self.source)
        default_data_file = "https://" + self.account_name +\
            ".file.core.windows.net/" + self.file_share + "/" +\
            os.path.basename(self.source)
        self.data_file = ctx.config['azure'].get('file_share', default_data_file)

        # get the preloaded workspace definition
        self.ws = Workspace.from_config()


    def _get_compute_target(self):
        if self.compute_cluster in self.ws.compute_targets:
            compute_target = self.ws.compute_targets[self.compute_cluster]
            if compute_target and type(compute_target) is AmlCompute:
                print('Found compute target. Just use it: ' + self.compute_cluster)
        else:
            print('Creating new AML compute context.')
            provisioning_config = AmlCompute.provisioning_configuration(
                vm_size=self.compute_sku, min_nodes=self.compute_min_nodes,
                max_nodes=self.compute_max_nodes)
            compute_target = ComputeTarget.create(
                self.ws, self.compute_cluster, provisioning_config)
            compute_target.wait_for_completion(show_output = True)
        return compute_target

    def import_data(self):
        ds = self.ws.get_default_datastore()
        ds.upload_files(files=[self.source], relative_root=None,
            target_path=None, overwrite=True, show_progress=True)

    def train(self):
        print('trainig on: ', os.path.basename(self.source))
        ds = self.ws.get_default_datastore()
        training_data = Dataset.Tabular.from_delimited_files(
            path=ds.path(os.path.basename(self.source)))
        # training_data.drop_columns(columns)

        compute_target = self._get_compute_target()

        automl_settings = {
            "name": "AutoML_Experiment_{0}".format(time.time()),
            "iteration_timeout_minutes" : self.iteration_timeout_minutes,
            "iterations" : self.max_n_trials,
            "primary_metric" : self.metric,
            "verbosity" : logging.DEBUG,
            "n_cross_validations": self.cross_validation_folds,
            "enable_stack_ensemble": self.use_ensemble
        }

        self.automl_config = AutoMLConfig(
            task=self.model_type,
            debug_log='automl_errors.log',
            path = os.getcwd(),
            compute_target = compute_target,
            training_data=training_data,
            label_column_name=self.target,
            **automl_settings)

        experiment=Experiment(self.ws, 'automl_remote')
        print("Submitting training run...")
        remote_run = experiment.submit(self.automl_config, show_output=False)
        print('remote_run: ', remote_run.run_id)

    def evaluate(self):
        run_id = self.ctx.config['azure'].get('experiment/run_id', None)
        if run_id:
            experiment = Experiment(self.ws, 'automl_remote')
            remote_run = AutoMLRun(experiment = experiment, run_id = run_id)
            self.ctx.log('Status: %s' % remote_run.get_status())
            summary = remote_run.summary()
            for model in summary:
                self.ctx.log('%s %s' % (model[0], model[2]))

            min_trail = self.max_n_trials - 10;
            if min_trail < 0:
                min_trail = 0;

            for index in range(min_trail, self.max_n_trials):
                best_run, fitted_model = remote_run.get_output(iteration=index)
                print('run_id: ', best_run)
                print('model: ', fitted_model)
        else:
            self.ctx.log('Pleae provide Run ID (experiment/run_id) to evaluate')

    def deploy(self):
        pass
    def predict(self,filepath,score_threshold):
        pass
    def review(self):
        pass
