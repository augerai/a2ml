import os
import time
import json
import logging
import numpy as np
import pandas as pd
import azureml.core
from azureml.core import Workspace
from azureml.core import Experiment
from azureml.core import diagnostic_log
from azureml.core.dataset import Dataset
from azureml.core.compute import AmlCompute
from azureml.core.compute import ComputeTarget
from azureml.train.automl import AutoMLConfig
from azureml.core.experiment import Experiment
from azureml.train.automl.run import AutoMLRun
# deployment
from azureml.core.model import InferenceConfig
from azureml.core.webservice import AciWebservice
from azureml.core.webservice import Webservice
from azureml.exceptions import WebserviceException
from azureml.core.model import Model

from a2ml.api import a2ml
from a2ml.api.utils.formatter import print_table

logging.basicConfig(level=logging.INFO)

class AzureA2ML(object):
    def __init__(self, ctx):
        diagnostic_log().start_capture()
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
            "verbosity" : logging.INFO,
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
        self.ctx.config['azure'].yaml['experiment']['run_id'] = remote_run.run_id
        self.ctx.config['azure'].write()

    def _get_leaderboard(self, remote_run):
        primary_metric = remote_run.properties['primary_metric']
        children = list(remote_run.get_children(recursive=True))
        leaderboard = pd.DataFrame(index=['model id', 'algorithm', 'score'])
        goal_minimize = False
        for run in children:
            if('run_algorithm' in run.properties and 'score' in run.properties):
                if(run.properties['run_preprocessor']):
                    run_algorithm = '%s,%s' % (run.properties['run_preprocessor'],
                        run.properties['run_algorithm'])
                else:
                    run_algorithm = run.properties['run_algorithm']
                leaderboard[run.id] = [run.id,
                                      run_algorithm,
                                      float(run.properties['score'])]
                if('goal' in run.properties):
                    goal_minimize = run.properties['goal'].split('_')[-1] == 'min'

        leaderboard = leaderboard.T.sort_values(
            'score', ascending = goal_minimize)
        leaderboard = leaderboard.head(10)
        leaderboard.rename(columns={'score':primary_metric}, inplace=True)
        return leaderboard

    def evaluate(self):
        run_id = self.ctx.config['azure'].get('experiment/run_id', None)
        if run_id:
            experiment = Experiment(self.ws, 'automl_remote')
            remote_run = AutoMLRun(experiment = experiment, run_id = run_id)
            leaderboard = self._get_leaderboard(remote_run)
            print_table(self.ctx.log,leaderboard.to_dict('records'))
            self.ctx.log('Status: %s' % remote_run.get_status())
        else:
            self.ctx.log('Pleae provide Run ID (experiment/run_id) to evaluate')

    def _aci_service_name(self, model_name):
        return (model_name+'-service').lower()

    def deploy(self, model_id, locally=False):
# samples
# https://github.com/Azure/MachineLearningNotebooks/blob/master/how-to-use-azureml/deployment/deploy-to-cloud/model-register-and-deploy.ipynb
# https://ml.azure.com/fileexplorer?wsid=/subscriptions/28ca7f62-a275-4222-aaa1-c8e9ec93adbb/resourceGroups/azure-iris_resources/workspaces/azure-iris_ws&tid=6d111df4-1dfb-481f-ac25-6ff206ab1ae0&activeFilePath=Samples/Python/1.0.83/how-to-use-azureml/automated-machine-learning/forecasting-orange-juice-sales/auto-ml-forecasting-orange-juice-sales.ipynb#Operationalize
        if (locally):
            print('Local deployment is not implemeted yet')
            return

        service_name = 'automl-remote'
        experiment_run_id = self.ctx.config['azure'].get(
            'experiment/run_id', None)

        experiment = Experiment(self.ws, 'automl_remote')
        remote_run = AutoMLRun(experiment = experiment, run_id = model_id)
        script_file_name = '.azureml/score_script.py'
        remote_run.download_file(
            'outputs/scoring_file_v_1_0_0.py', script_file_name)
        model_name = remote_run.properties['model_name']
        print('model_name: ', model_name)

        description = '%s-%s' % (service_name, model_name)
        print('description: ', description)
        experiment_run = AutoMLRun(
            experiment = experiment, run_id = experiment_run_id)
        # do we need to check for already registered one?
        model = experiment_run.register_model(
            model_name = model_name,
            description = description,
            tags = None)

        print('Deploying AciWebservice...')

        inference_config = InferenceConfig(
            environment = remote_run.get_environment(),
            entry_script = script_file_name)

        aciconfig = AciWebservice.deploy_configuration(
            cpu_cores = 1,
            memory_gb = 2,
            tags = {'type': "%s-inference-service" % service_name},
            description = "%s inference service" % service_name)

        # It must only consist of lowercase letters, numbers, or dashes, start
        # with a letter, end with a letter or number, and be between 3 and 32
        # characters long.
        # TBD - service_name + suffix must satisfy requiremets
        aci_service_name = self._aci_service_name(model_name)
        print(aci_service_name)

        # Remove any existing service under the same name.
        try:
            Webservice(self.ws, aci_service_name).delete()
        except WebserviceException:
            pass

        aci_service = Model.deploy(
            self.ws,
            aci_service_name,
            [model],
            inference_config,
            aciconfig)
        aci_service.wait_for_deployment(True)
        print(aci_service.state)

    def predict(self, filename, model_id, threshold=None, locally=False):
        if (locally):
            print('Local predict is not implemeted yet...')
            return

        # TBD - add exclude to DataFrame.load_records
        from auger.api.cloud.utils.dataframe import DataFrame
        target = self.ctx.config['config'].get('target', None)
        records, features = DataFrame.load_records(filename, target)
        input_payload = json.dumps({'data': records})

        experiment = Experiment(self.ws, 'automl_remote')
        remote_run = AutoMLRun(experiment = experiment, run_id = model_id)
        model_name = remote_run.properties['model_name']

        aci_service_name = self._aci_service_name(model_name)
        aci_service = AciWebservice(self.ws, aci_service_name)
        response = aci_service.run(input_data = input_payload)

        rcdf = pd.DataFrame(records, columns = features)
        rsdf = pd.DataFrame(
            json.loads(response)['result'], columns = [target])
        predictions = pd.concat([rcdf, rsdf], axis=1)
        predicted = os.path.abspath(
            os.path.splitext(filename)[0] + "_predicted.csv")
        predictions.to_csv(predicted, index=False, encoding='utf-8')
        self.ctx.log('Predictions are saved to %s' % predicted)

    def review(self):
        pass
