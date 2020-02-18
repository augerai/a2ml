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
        self.experiment_name = ctx.config['config'].get('name', 'automl_remote')

        # get the preloaded workspace definition
        self.ws = Workspace.from_config()

    def _get_compute_target(self):
        compute_min_nodes = self.ctx.config['azure'].get('cluster/min_nodes',1)
        compute_max_nodes = self.ctx.config['azure'].get('cluster/max_nodes',4)
        compute_sku = self.ctx.config['azure'].get('cluster/type','STANDARD_D2_V2')
        compute_cluster = self.ctx.config['azure'].get('cluster/name','cpu-cluster')

        if compute_cluster in self.ws.compute_targets:
            compute_target = self.ws.compute_targets[compute_cluster]
            if compute_target and type(compute_target) is AmlCompute:
                print('Found compute target. Just use it: ' + compute_cluster)
        else:
            print('Creating new AML compute context.')
            provisioning_config = AmlCompute.provisioning_configuration(
                vm_size=compute_sku, min_nodes=compute_min_nodes,
                max_nodes=compute_max_nodes)
            compute_target = ComputeTarget.create(
                self.ws, compute_cluster, provisioning_config)
            compute_target.wait_for_completion(show_output = True)
        return compute_target

    def import_data(self):
        source = self.ctx.config['config'].get('source', None)
        ds = self.ws.get_default_datastore()
        ds.upload_files(files=[source], relative_root=None,
            target_path=None, overwrite=True, show_progress=True)

    def train(self):
        config = self.ctx.config['config']
        source = config.get('source', None)
        print('trainig on: ', os.path.basename(source))
        ds = self.ws.get_default_datastore()
        training_data = Dataset.Tabular.from_delimited_files(
            path=ds.path(os.path.basename(source)))
        # training_data.drop_columns(columns)

        compute_target = self._get_compute_target()

        model_type = config.get('model_type')
        if (not model_type):
            raise Exception('Please specify model_type')
        primary_metric = self.ctx.config['azure'].get('experiment/metric','spearman_correlation')
        #TODO: check model_type and set primary_metric

        automl_settings = {
            #"name": "AutoML_Experiment_{0}".format(time.time()),
            "iteration_timeout_minutes" : config.get('experiment/iteration_timeout_minutes',10),
            "iterations" : config.get('experiment/max_n_trials',10),
            "primary_metric" : primary_metric,
            "verbosity" : logging.INFO,
            "n_cross_validations": config.get('experiment/cross_validation_folds',5),
            "enable_stack_ensemble": config.get('experiment/use_ensemble',False)
        }

        self.automl_config = AutoMLConfig(
            task=model_type,
            debug_log='automl_errors.log',
            path = os.getcwd(),
            compute_target = compute_target,
            training_data=training_data,
            label_column_name=config.get('target'),
            **automl_settings)

        experiment=Experiment(self.ws, self.experiment_name)
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
            experiment = Experiment(self.ws, self.experiment_name)
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

        experiment = Experiment(self.ws, self.experiment_name)
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

    def _save_predictions(self, df_predictions, filename):
        predicted_path = os.path.abspath(
            os.path.splitext(filename)[0] + "_predicted.csv")
        df_predictions.to_csv(predicted_path, index=False, encoding='utf-8')
        self.ctx.log('Predictions are saved to %s' % predicted_path)
        
    def _predict_local(self, predict_data, model_id, threshold):
        from auger.api.cloud.utils.dataframe import DataFrame

        experiment = Experiment(self.ws, self.experiment_name)
        run_id = model_id
        iteration = None
        parts = model_id.split('_')
        if len(parts) > 2:
            run_id = parts[0]+"_"+parts[1]
            iteration = parts[2]

        #print(run_id)
        #print(iteration)    
        remote_run = AutoMLRun(experiment = experiment, run_id = run_id)
        best_run, fitted_model = remote_run.get_output(iteration=iteration)

        return fitted_model.predict(predict_data)

    def predict(self, filename, model_id, threshold=None, locally=False):
        from auger.api.cloud.utils.dataframe import DataFrame
        target = self.ctx.config['config'].get('target', None)
        predict_data = DataFrame.load(filename, target)

        y_pred = []
        if (locally):
            y_pred = self._predict_local(predict_data, model_id, threshold)
        else:    
            input_payload = predict_data.to_json(orient='split', index=False)
            # import requests
            # headers = {'Content-Type': 'application/json; charset=utf-8'}
            # scoring_uri = 'http://b2ddd7c1-697e-43a5-b050-ba48a77cbb56.eastus2.azurecontainer.io/score'
            # resp = requests.post(scoring_uri, input_payload, headers=headers)
            # print(resp.text)

            experiment = Experiment(self.ws, self.experiment_name)
            remote_run = AutoMLRun(experiment = experiment, run_id = model_id)
            model_name = remote_run.properties['model_name']

            aci_service_name = self._aci_service_name(model_name)
            aci_service = AciWebservice(self.ws, aci_service_name)
            input_payload = json.loads(input_payload)
            input_payload = {
                'method': 'predict',
                'data': input_payload['data']
            }
            input_payload = json.dumps(input_payload)
            #print(input_payload)

            response = aci_service.run(input_data = input_payload)
            y_pred = json.loads(response)['result']

        predict_data[target] = y_pred
        self._save_predictions(predict_data, filename)

    def review(self):
        pass
