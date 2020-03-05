import os
import time
import json
import logging
import numpy as np
import pandas as pd
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
from a2ml.api.azure.decorators import error_handler
from a2ml.api.azure.exceptions import AzureException

logging.basicConfig(level=logging.INFO)


class AzureA2ML(object):
    def __init__(self, ctx):
        diagnostic_log().start_capture()
        self.ctx = ctx
        project_name = self.ctx.config.get('name', '')
        self.experiment_name = ctx.config.get('experiment/name', project_name)
        self.cluster_name = self.ctx.config.get('cluster/name', project_name)

        # get the preloaded workspace definition
        self.ws = Workspace.from_config()

    def _get_compute_target(self):
        compute_min_nodes = self.ctx.config.get('cluster/min_nodes',1)
        compute_max_nodes = self.ctx.config.get('cluster/max_nodes',4)
        compute_sku = self.ctx.config.get('cluster/type','STANDARD_D2_V2')
        compute_cluster = self.cluster_name

        if compute_cluster in self.ws.compute_targets:
            compute_target = self.ws.compute_targets[compute_cluster]
            if compute_target and type(compute_target) is AmlCompute:
                self.ctx.log(
                    'Found compute target. Just use it: ' + compute_cluster)
        else:
            self.ctx.log('Creating new AML compute context...')
            provisioning_config = AmlCompute.provisioning_configuration(
                vm_size=compute_sku, min_nodes=compute_min_nodes,
                max_nodes=compute_max_nodes)
            compute_target = ComputeTarget.create(
                self.ws, compute_cluster, provisioning_config)
            compute_target.wait_for_completion(show_output = True)
        return compute_target

    @error_handler
    def import_data(self):
        source = self.ctx.config.get('source', None)
        if source is None:
            raise AzureException('Please specify data source file...')
        ds = self.ws.get_default_datastore()
        ds.upload_files(files=[source], relative_root=None,
            target_path=None, overwrite=True, show_progress=True)
        dataset = os.path.basename(source)
        self.ctx.config.set('azure', 'dataset', dataset)
        self.ctx.config.write('azure')
        return {'dataset': dataset}

    @error_handler
    def train(self):
        config = self.ctx.config
        dataset = config.get('dataset', None)
        self.ctx.log("Starting search on %s Dataset..." % dataset)
        ds = self.ws.get_default_datastore()
        training_data = Dataset.Tabular.from_delimited_files(
            path=ds.path(dataset))
        #TODO training_data.drop_columns(columns)

        compute_target = self._get_compute_target()

        model_type = config.get('model_type')
        if (not model_type):
            raise AzureException('Please specify model type...')
        primary_metric = config.get('experiment/metric','spearman_correlation')
        if (not primary_metric):
            raise AzureException('Please specify primary metric...')
        #TODO: check if primary_metric is constent with model_type

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
        remote_run = experiment.submit(self.automl_config, show_output=False)
        self.ctx.log("Started Experiment %s search..." % self.experiment_name)
        config.set('azure', 'experiment/name', self.experiment_name)
        config.set('azure', 'experiment/run_id', remote_run.run_id)
        config.write('azure')
        return {
            'eperiment_name': self.experiment_name,
            'run_id': remote_run.run_id}

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

    @error_handler
    def evaluate(self, run_id = None):
        if run_id is None:
            run_id = self.ctx.config.get('experiment/run_id', None)
        if run_id is None:
            raise AzureException(
                'Pleae provide Run ID (experiment/run_id) to evaluate')
        experiment = Experiment(self.ws, self.experiment_name)
        remote_run = AutoMLRun(experiment = experiment, run_id = run_id)
        leaderboard = self._get_leaderboard(remote_run).to_dict('records')
        print_table(self.ctx.log,leaderboard)
        status = remote_run.get_status()
        self.ctx.log('Status: %s' % status)
        return {
            'run_id': run_id,
            'leaderboard': leaderboard,
            'status': status }

    def _aci_service_name(self, model_name):
        return (model_name+'-service').lower()

    @error_handler
    def deploy(self, model_id, locally=False):
        if (locally):
            self.ctx.log('Local deployment step is not required for Azure..')
            return {'model_id': model_id}

        service_name = 'automl-remote'
        experiment_run_id = self.ctx.config.get(
            'experiment/run_id', None)

        experiment = Experiment(self.ws, self.experiment_name)
        remote_run = AutoMLRun(experiment = experiment, run_id = model_id)
        script_file_name = '.azureml/score_script.py'
        remote_run.download_file(
            'outputs/scoring_file_v_1_0_0.py', script_file_name)
        model_name = remote_run.properties['model_name']
        self.ctx.log('Model name: %s' % model_name)

        description = '%s-%s' % (service_name, model_name)
        experiment_run = AutoMLRun(
            experiment = experiment, run_id = experiment_run_id)
        # do we need to check for already registered one?
        model = experiment_run.register_model(
            model_name = model_name,
            description = description,
            tags = None)

        # It must only consist of lowercase letters, numbers, or dashes, start
        # with a letter, end with a letter or number, and be between 3 and 32
        # characters long.
        # TBD - service_name + suffix must satisfy requiremets
        aci_service_name = self._aci_service_name(model_name)
        self.ctx.log('Deploying AciWebservice %s ...' % aci_service_name)

        inference_config = InferenceConfig(
            environment = remote_run.get_environment(),
            entry_script = script_file_name)

        aciconfig = AciWebservice.deploy_configuration(
            cpu_cores = 1,
            memory_gb = 2,
            tags = {'type': "%s-inference-service" % service_name},
            description = "%s inference service" % service_name)

        # Remove any existing service under the same name.
        try:
            Webservice(self.ws, aci_service_name).delete()
            self.ctx.log('Remove any existing service under the same name...')
        except WebserviceException:
            pass

        aci_service = Model.deploy(
            self.ws,
            aci_service_name,
            [model],
            inference_config,
            aciconfig)
        aci_service.wait_for_deployment(True)
        self.ctx.log('%s state %s' % (aci_service_name, str(aci_service.state)))

        return {'model_id': model_id, 'aci_service_name': aci_service_name}

    def _save_predictions(self, df_predictions, filename):
        predicted_path = os.path.abspath(
            os.path.splitext(filename)[0] + "_predicted.csv")
        df_predictions.to_csv(predicted_path, index=False, encoding='utf-8')
        self.ctx.log('Predictions are saved to %s' % predicted_path)
        return predicted_path

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

    @error_handler
    def predict(self, filename, model_id, threshold=None, locally=False):
        from auger.api.cloud.utils.dataframe import DataFrame
        target = self.ctx.config.get('target', None)
        predict_data = DataFrame.load(filename, target)

        y_pred = []
        if (locally):
            y_pred = self._predict_local(predict_data, model_id, threshold)
        else:
            input_payload = predict_data.to_json(orient='split', index=False)

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

            response = aci_service.run(input_data = input_payload)
            y_pred = json.loads(response)['result']

        predict_data[target] = y_pred
        predicted = self._save_predictions(predict_data, filename)

        return {'predicted': predicted}

    def review(self):
        pass
