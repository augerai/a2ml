import os
import json
from azureml.core import Experiment
from azureml.core.model import Model
from azureml.core.model import InferenceConfig
from azureml.core.webservice import Webservice
from azureml.core.webservice import AciWebservice
from azureml.exceptions import WebserviceException
from azureml.train.automl.run import AutoMLRun
from .project import AzureProject
from .exceptions import AzureException
from .decorators import error_handler
from auger.api.cloud.utils.dataframe import DataFrame


class AzureModel(object):

    def __init__(self, ctx):
        super(AzureModel, self).__init__()
        self.ctx = ctx

    @error_handler
    def deploy(self, model_id, locally):
        if locally:
            self.ctx.log('Local deployment step is not required for Azure..')
            return {'model_id': model_id}

        ws = AzureProject(self.ctx)._get_ws()
        experiment_name = self.ctx.config.get('experiment/name', None)
        if experiment_name is None:
            raise AzureException('Please specify Experiment name...')

        iteration, run_id = self._get_iteration(model_id)

        experiment = Experiment(ws, experiment_name)
        experiment_run = AutoMLRun(experiment = experiment, run_id = run_id)
        model_run = AutoMLRun(experiment = experiment, run_id = model_id)
        model_name = model_run.properties['model_name']
        self.ctx.log('Regestiring model: %s' % model_name)

        description = '%s-%s' % (model_name, iteration)
        model = experiment_run.register_model(
            model_name = model_name, iteration=iteration,
            description = description, tags = None)

        script_file_name = '.azureml/score_script.py'
        model_run.download_file(
            'outputs/scoring_file_v_1_0_0.py', script_file_name)

        # Deploying ACI Service
        aci_service_name = self._aci_service_name(model_name)
        self.ctx.log('Deploying AciWebservice %s ...' % aci_service_name)

        inference_config = InferenceConfig(
            environment = model_run.get_environment(),
            entry_script = script_file_name)

        aciconfig = AciWebservice.deploy_configuration(
            cpu_cores = 1,
            memory_gb = 2,
            tags = {'type': "inference-%s" % aci_service_name},
            description = "inference-%s" % aci_service_name)

        # Remove any existing service under the same name.
        try:
            Webservice(ws, aci_service_name).delete()
            self.ctx.log('Remove any existing service under the same name...')
        except WebserviceException:
            pass

        aci_service = Model.deploy(
            ws, aci_service_name, [model], inference_config, aciconfig)
        aci_service.wait_for_deployment(True)
        self.ctx.log('%s state %s' % (aci_service_name, str(aci_service.state)))

        return {'model_id': model_id, 'aci_service_name': aci_service_name}

    @error_handler
    def predict(self, filename, model_id, threshold, locally):
        ws = AzureProject(self.ctx)._get_ws()
        experiment_name = self.ctx.config.get('experiment/name', None)
        if experiment_name is None:
            raise AzureException('Please specify Experiment name...')
        experiment = Experiment(ws, experiment_name)

        target = self.ctx.config.get('target', None)
        predict_data = DataFrame.load(filename, target)

        y_pred = []
        if locally:
            y_pred = self._predict_locally(
                experiment, predict_data, model_id, threshold)
        else:
            y_pred = self._predict_remotely(
                ws, experiment, predict_data, model_id, threshold)

        predict_data[target] = y_pred
        predicted = self._save_predictions(predict_data, filename)

        return {'predicted': predicted}

    @error_handler        
    def actual(self, filename, model_id):
        pass

    def _get_iteration(self, model_id):
        iteration = None
        run_id = model_id
        parts = model_id.split('_')
        if len(parts) > 2:
            run_id = parts[0]+"_"+parts[1]
            iteration = parts[2]
        return iteration, run_id

    def _aci_service_name(self, model_name):
        # It must only consist of lowercase letters, numbers, or dashes, start
        # with a letter, end with a letter or number, and be between 3 and 32
        # characters long.
        #TODO - service_name + suffix must satisfy requiremets
        return (model_name+'-service').lower()

    def _predict_remotely(
        self, ws, experiment, predict_data, model_id, threshold):
        input_payload = predict_data.to_json(orient='split', index = False)

        remote_run = AutoMLRun(experiment = experiment, run_id = model_id)
        model_name = remote_run.properties['model_name']
        aci_service_name = self._aci_service_name(model_name)
        aci_service = AciWebservice(ws, aci_service_name)

        input_payload = json.loads(input_payload)
        input_payload = {
            'method': 'predict',
            'data': input_payload['data']
        }
        input_payload = json.dumps(input_payload)
        try:
            response = aci_service.run(input_data = input_payload)
        except Exception as e:
            print('err log', aci_service.get_logs())
            raise e
        return json.loads(response)['result']

    def _predict_locally(self, experiment, predict_data, model_id, threshold):
        run_id = model_id
        iteration = None
        parts = model_id.split('_')
        if len(parts) > 2:
            run_id = parts[0]+"_"+parts[1]
            iteration = parts[2]

        remote_run = AutoMLRun(experiment = experiment, run_id = run_id)
        best_run, fitted_model = remote_run.get_output(iteration=iteration)

        return fitted_model.predict(predict_data)

    def _save_predictions(self, df_predictions, filename):
        predicted_path = os.path.abspath(
            os.path.splitext(filename)[0] + "_predicted.csv")
        df_predictions.to_csv(predicted_path, index=False, encoding='utf-8')
        self.ctx.log('Predictions are saved to %s' % predicted_path)
        return predicted_path
