import os
import json
import time

from .exceptions import AzureException
from a2ml.api.utils.dataframe import DataFrame
from a2ml.api.utils import fsclient, retry_helper
from a2ml.api.utils.decorators import error_handler, authenticated
from a2ml.api.model_review.model_helper import ModelHelper
from a2ml.api.model_review.model_review import ModelReview
from .credentials import Credentials


class AzureModel(object):

    def __init__(self, ctx):
        super(AzureModel, self).__init__()
        self.ctx = ctx
        self.credentials = Credentials(self.ctx).load()

    @error_handler
    @authenticated
    def deploy(self, model_id, locally, review, name=None):
        if locally:
            is_loaded, model_path = self.verify_local_model(model_id)
            if is_loaded:
                self.ctx.log('Model already deployed to %s' % model_path)
                return {'model_id': model_id}

        from azureml.train.automl.run import AutoMLRun

        ws, experiment = self._get_experiment()
        model_run = AutoMLRun(experiment = experiment, run_id = model_id)

        # result = self._deploy_locally(model_id, model_run, ws, experiment) if locally else \
        #     self._deploy_remotly(model_id, model_run, ws, experiment)
        result = True

        model_features, target_categories = self._get_remote_model_features(model_run)
        feature_importance = self._get_feature_importance(model_run)

        options = {
            'uid': model_id,
            'targetFeature': self.ctx.config.get('target'),
            'support_review_model': review,
            'provider': self.ctx.config.name,
            'scoreNames': [self.ctx.config.get('experiment/metric')],
            'scoring': self.ctx.config.get('experiment/metric'),
            "score_name": self.ctx.config.get('experiment/metric'),
            "review_metric": self.ctx.config.get('experiment/review_metric'),
            "originalFeatureColumns": model_features,
            "model_type": self.ctx.config.get("model_type")
        }
        options.update(self._get_hub_info())
        fsclient.write_json_file(os.path.join(self.ctx.config.get_model_path(model_id), "options.json"),
            options)
        target_categoricals = {}
        if target_categories:
            target_categoricals = {self.ctx.config.get('target'): {"categories": target_categories}}
        fsclient.write_json_file(os.path.join(self.ctx.config.get_model_path(model_id), "target_categoricals.json"),
            target_categoricals )

        metric_path = ModelHelper.get_metric_path( options, model_id)
        if metric_path:
            fsclient.write_json_file(os.path.join(metric_path, "metric_names_feature_importance.json"),
                {'feature_importance_data': {
                    'features': list(feature_importance.keys()),
                    'scores': list(feature_importance.values())
                }})

        return result

    def _get_hub_info(self):
        return {'hub_info':{
                'project_path': self.ctx.config.get_path(),
                'experiment_id': self.ctx.config.get('experiment/hub_experiment_id', None),
                'experiment_session_id':self.ctx.config.get('experiment/hub_session_id', None),
            }};

    def _deploy_remotly(self, model_id, model_run, ws, experiment):
        from azureml.core.model import Model
        from azureml.core.model import InferenceConfig
        from azureml.train.automl.run import AutoMLRun

        # ws, experiment = self._get_experiment()
        iteration, run_id = self._get_iteration(model_id)

        experiment_run = AutoMLRun(experiment = experiment, run_id = run_id)
        model_name = model_run.properties['model_name']
        self.ctx.log('Registering model: %s' % model_id)

        description = '%s-%s' % (model_name, iteration)
        model = experiment_run.register_model(
            model_name = model_name, iteration=iteration,
            description = description, tags = None)

        script_file_name = '.azureml/score_script.py'
        model_run.download_file(
            'outputs/scoring_file_v_1_0_0.py', script_file_name)

        self._edit_score_script(script_file_name)

        service_name, service_config, service_target = \
            self._create_deploy_service(model_name, ws)

        inference_config = InferenceConfig(
            environment = model_run.get_environment(),
            entry_script = script_file_name)

        deploy_service = Model.deploy(
            ws, service_name, [model], inference_config, deployment_config=service_config,
            deployment_target=service_target, overwrite=True)
        deploy_service.wait_for_deployment(show_output=True)
        self.ctx.log('%s state %s' % (service_name, str(deploy_service.state)))

        return {'model_id': model_id, 'service_name': service_name}

    def _create_deploy_service(self, model_name, ws):
        from azureml.core.webservice import AciWebservice, AksWebservice, Webservice
        from azureml.exceptions import WebserviceException
        from azureml.core.compute import AksCompute, ComputeTarget
        from .project import AzureProject

        service_type = self.ctx.config.get('deploy_cluster/type', 'aci').lower()
        cpu_cores = float(self.ctx.config.get('deploy_cluster/cpu_cores', 1))
        memory_gb = float(self.ctx.config.get('deploy_cluster/memory_gb', 2))
        service_name = self._deploy_service_name(model_name)
        service_target = None

        if service_type == "aci":
            self.ctx.log('Deploying AciWebservice %s ...' % service_name)

            service_config = AciWebservice.deploy_configuration(
                cpu_cores = cpu_cores,
                memory_gb = memory_gb,
                tags = {'type': "inference-%s" % service_name},
                description = "inference-%s" % service_name)
        elif service_type == "aks":
            self.ctx.log('Deploying AksWebservice %s ...' % service_name)
            aks_compute_target = AzureProject._fix_cluster_name(
                self.ctx.config.get('deploy_cluster/compute_target', "a2ml_aks_deploy"))
            if not aks_compute_target in ws.compute_targets:
                if self.ctx.is_runs_on_server():
                    raise AzureException("Compute target %s does not exist."%aks_compute_target)

                self.ctx.log('Creating AksCompute %s ...' % aks_compute_target)
                prov_config = AksCompute.provisioning_configuration(
                    agent_count=int(self.ctx.config.get('deploy_cluster/agent_count', 2)),
                    vm_size=self.ctx.config.get('deploy_cluster/vm_size', "STANDARD_D2_V2"),
                    cluster_purpose=self.ctx.config.get('deploy_cluster/purpose', AksCompute.ClusterPurpose.DEV_TEST)
                )
                service_target = ComputeTarget.create(workspace = ws,
                                name = aks_compute_target,
                                provisioning_configuration = prov_config)

                # Wait for the create process to complete
                service_target.wait_for_completion(show_output = True)
            else:
                service_target = AksCompute(ws, aks_compute_target)

            service_config = AksWebservice.deploy_configuration(
                cpu_cores = cpu_cores,
                memory_gb = memory_gb)
        else:
            raise AzureException("deploy_cluster/type: %s it not supported. Supported type: aci, aks"%service_type)

        try:
            Webservice(ws, service_name).delete()
        except WebserviceException as exc:
            self.ctx.log("Delete existing service failed: %s"%exc.message)

        return service_name, service_config, service_target

    def _get_deploy_service(self, model_name, ws):
        from azureml.core.webservice import AciWebservice, AksWebservice

        service_name = self._deploy_service_name(model_name)
        service_type = self.ctx.config.get('deploy_cluster/type', 'aci').lower()

        if service_type == "aci":
            deploy_service = AciWebservice(ws, service_name)
        elif service_type == "aks":
            deploy_service = AksWebservice(ws, service_name)
        else:
            raise AzureException("deploy_cluster/type: %s it not supported. Supported type: aci, aks"%service_type)

        return deploy_service

    def _edit_score_script(self, script_file_name):
        text = fsclient.read_text_file(script_file_name)

        text = text.replace("@input_schema('data', PandasParameterType(input_sample))",
        """
def convert_simple_numpy_type(obj):
    if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
        np.int16, np.int32, np.int64, np.uint8,
        np.uint16, np.uint32, np.uint64)):
        return int(obj)
    elif isinstance(obj, (np.float_, np.float16, np.float32,
        np.float64)):
        return float(obj)

    return None

class NumpyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        res = convert_simple_numpy_type(obj)
        if res is not None:
            return res

        return json.JSONEncoder.default(self, obj)

def json_dumps_np(data, allow_nan=True):
    return json.dumps(data, cls=NumpyJSONEncoder, allow_nan=allow_nan)

@input_schema('data', PandasParameterType(input_sample))
def get_df(data):
    return data

        """
        )

        text = text.replace("result = model.predict(data)",
        """
        df = get_df(data['data'])
        proba_classes = []
        if data['method'] == "predict_proba":
            result = model.predict_proba(df)
            proba_classes = list(model.classes_)
        else:
            result = model.predict(df)

        """
        )

        text = text.replace("return json.dumps({\"result\": result.tolist()})",
            "return json_dumps_np({\"result\": result.tolist(), \"proba_classes\": proba_classes})")
        fsclient.write_text_file(script_file_name, text)

    @error_handler
    @authenticated
    def predict(self, filename, model_id, threshold=None, locally=False, data=None, columns=None,
        predicted_at=None, output=None, json_result=False, count_in_result=False, prediction_id=None
        ):
        ds = DataFrame.create_dataframe(filename, data, columns)
        model_path = self.ctx.config.get_model_path(model_id)
        options = fsclient.read_json_file(os.path.join(model_path, "options.json"))

        if threshold and options.get('model_type', 'classification') != 'classification':
            self.ctx.log("Threshold only applied to classification and will be ignored.")
            threshold = None

        results, results_proba, proba_classes, target_categories, model_features = \
            self._predict_locally(ds.df, model_id, threshold) if locally else self._predict_remotely(ds.df, model_id, threshold)

        if target_categories and len(target_categories) == 2:
            for idx, item in enumerate(target_categories):
                if item == "False":
                    target_categories[idx] = False
                if item == "True":
                    target_categories[idx] = True

        target_feature = options.get('targetFeature', self.ctx.config.get('target', None))
        ModelHelper.process_prediction(ds,
            results, results_proba, proba_classes,
            threshold,
            options.get('minority_target_class', self.ctx.config.get('minority_target_class')),
            target_feature,
            target_categories)

        gzip_predict_file = False
        if ds.count() > options.get('max_predict_records_to_gzip', 1000):
            gzip_predict_file = True

        if model_features:
            model_features += [target_feature]

        predicted = ModelHelper.save_prediction(ds, prediction_id,
            json_result, count_in_result, predicted_at,
            model_path, model_id, output, gzip_predict_file=gzip_predict_file, model_features=model_features)

        if filename:
            self.ctx.log('Predictions stored in %s' % predicted)

        return {'predicted': predicted}

    @error_handler
    @authenticated
    def actuals(self, model_id, filename=None, data=None, columns=None, actuals_at=None, actual_date_column=None, locally=False):
        if locally:
            model_path = self.ctx.config.get_model_path(model_id)

            if not fsclient.is_folder_exists(model_path):
                raise Exception('Model should be deployed first.')

            return ModelReview({'model_path': model_path}).add_actuals(
                self.ctx,
                actuals_path=filename,
                data=data,
                columns=columns,
                actual_date=actuals_at,
                actual_date_column=actual_date_column,
                provider='azure'
            )
        else:
            raise Exception("Not Implemented")

    @error_handler
    @authenticated
    def delete_actuals(self, model_id, with_predictions=False, begin_date=None, end_date=None, locally=False):
        if locally:
            model_path = self.ctx.config.get_model_path(model_id)

            if not fsclient.is_folder_exists(model_path):
                raise Exception('Model should be deployed first.')

            return ModelReview({'model_path': model_path}).delete_actuals(
                with_predictions=with_predictions, begin_date=begin_date, end_date=end_date)
        else:
            raise Exception("Not Implemented")

    @error_handler
    @authenticated
    def build_review_data(self, model_id, locally, output):
        if locally:
            model_path = self.ctx.config.get_model_path(model_id)

            if not fsclient.is_folder_exists(model_path):
                raise Exception('Model should be deployed first.')

            return ModelReview({'model_path': os.path.join(model_path, "model")}).build_review_data(
              data_path=self.ctx.config.get("source"), output=output)
        else:
            raise Exception("Not Implemented.")

    def _get_iteration(self, model_id):
        iteration = None
        run_id = model_id
        parts = model_id.split('_')
        if len(parts) > 2:
            run_id = parts[0]+"_"+parts[1]
            iteration = parts[2]
        return iteration, run_id

    def _deploy_service_name(self, model_name):
        # It must only consist of lowercase letters, numbers, or dashes, start
        # with a letter, end with a letter or number, and be between 3 and 32
        # characters long.
        #TODO - service_name + suffix must satisfy requiremets
        if model_name.endswith('-service'):
            return model_name

        return (model_name+'-service').lower()

    def _get_experiment(self):
        from azureml.core import Experiment
        from .project import AzureProject

        ws = AzureProject(self.ctx)._get_ws()
        experiment_name = self.ctx.config.get('experiment/name', None)
        if experiment_name is None:
            raise AzureException('Please specify Experiment name...')
        experiment = Experiment(ws, experiment_name)

        return ws, experiment

    def _get_remote_model_features(self, remote_run):
        from  a2ml.api.utils import fsclient, local_fsclient
        import pandas as pd

        model_features = None
        target_categories = None

        temp_dir = local_fsclient.LocalFSClient().get_temp_folder()
        try:
            file_name = 'scoring_file_v_1_0_0.py'
            remote_run.download_file('outputs/%s'%file_name, os.path.join(temp_dir, file_name))
            text = fsclient.read_text_file(os.path.join(temp_dir, file_name))
            to_find = "input_sample ="
            start = text.find(to_find)
            if start > 0:
                end = text.find("\n", start)
                if end > start:
                    code_to_run = text[start+len(to_find):end]

                    input_sample = eval(code_to_run)
                    model_features = input_sample.columns.tolist()
        except Exception as e:
            self.ctx.log('Cannot get columns from remote model.Use original columns from predicted data: %s'%e)

        if self.ctx.config.get("model_type") == "classification":
            try:
                file_name = 'confusion_matrix'
                remote_run.download_file('%s'%file_name, os.path.join(temp_dir, file_name))
                cm_data = fsclient.read_json_file(os.path.join(temp_dir, file_name))
                target_categories = cm_data.get('data', {}).get('class_labels')
            except Exception as e:
                self.ctx.log('Cannot get categorical target class labels from remote model.Use class codes: %s'%e)

        fsclient.remove_folder(temp_dir)
        return model_features, target_categories

    def _get_feature_importance(self, model_run):
        from azureml.interpret._internal.explanation_client import ExplanationClient

        try:
            client = ExplanationClient.from_run(model_run)
            engineered_explanations = client.download_model_explanation(raw=True)
            return engineered_explanations.get_feature_importance_dict()
        except Exception as e:
            self.ctx.log('Cannot get feature_importance from remote model: %s'%e)

        return {}

    def _call_service_run(self, deploy_service, input_data):
        return deploy_service.run(input_data = input_data)

    def _predict_remotely(self, predict_data, model_id, predict_proba):
        from azureml.train.automl.run import AutoMLRun
        from azureml.core.run import Run

        import numpy as np

        ws, experiment = self._get_experiment()

        model_features = None
        target_categories = None

        remote_run = AutoMLRun(experiment = experiment, run_id = model_id)
        model_features, target_categories = self._get_remote_model_features(remote_run)
        if model_id.startswith("AutoML_"):
            model_name = remote_run.properties['model_name']
        else:
            model_name = model_id

        if model_features:
            predict_data = predict_data[model_features]

        input_payload = predict_data.to_json(orient='split', index = False)
        input_payload = json.loads(input_payload)
        # If you have a classification model, you can get probabilities by changing this to 'predict_proba'.
        method = 'predict'
        if predict_proba:
            method = 'predict_proba'
        input_payload = {
            'data': {'data': input_payload['data'], 'method': method}
        }
        input_payload = json.dumps(input_payload)

        deploy_service = self._get_deploy_service(model_name, ws)

        try:
            response = retry_helper(lambda: self._call_service_run(deploy_service, input_payload),
                ['Connection aborted','Too many requests for service','WebserviceException'], ctx=self.ctx)
        except Exception as e:
            log_file = 'automl_errors.log'
            fsclient.write_text_file(log_file, deploy_service.get_logs(), mode="a")
            raise AzureException("Prediction service error. Please redeploy the model. Log saved to file '%s'. Details: %s"%(log_file, str(e)))

        response = json.loads(response)
        if "error" in response or not 'result' in response:
            raise AzureException('Prediction service return error: %s'%response.get('error'))

        results_proba = None
        proba_classes = None
        results = response['result']
        if predict_proba:
            results_proba = results
            proba_classes = response['proba_classes']
            results_proba = np.array(results_proba)

        return results, results_proba, proba_classes, target_categories, model_features

    def verify_local_model(self, model_id):
        model_path = os.path.join(self.ctx.config.get_model_path(model_id),
            'model.pkl.gz')
        return fsclient.is_file_exists(model_path), model_path

    def _deploy_locally(self, model_id, model_run, ws, experiment):
        from azureml.train.automl.run import AutoMLRun

        self.ctx.log('Downloading model %s' % model_id)

        iteration, run_id = self._get_iteration(model_id)
        remote_run = AutoMLRun(experiment = experiment, run_id = run_id)
        best_run, fitted_model = remote_run.get_output(iteration=iteration)

        is_loaded, model_path = self.verify_local_model(model_id)
        fsclient.save_object_to_file(fitted_model, model_path)

        # model_path = self.ctx.config.get_model_path(model_id)
        # with fsclient.save_local(os.path.join(model_path, 'model.pkl'), move_file=True) as local_path:
        #     model_run.download_file("outputs/model.pkl", local_path)

        self.ctx.log('Downloaded model to %s' % model_path)
        return {'model_id': model_id}

    def _predict_locally(self, predict_data, model_id, threshold):
        is_loaded, model_path = self.verify_local_model(model_id)
        if not is_loaded:
            raise Exception("Model should be deployed before predict.")

        fitted_model = fsclient.load_object_from_file(model_path, use_local_cache=True)
        model_features = None
        try:
            options = fsclient.read_json_file(os.path.join(self.ctx.config.get_model_path(model_id), "options.json"))

            model_features = options.get("originalFeatureColumns")
            predict_data = predict_data[model_features]
            predict_data.to_csv("test_options.csv", index=False, compression=None, encoding='utf-8')
        except Exception as e:
            self.ctx.log('Cannot get columns from model.Use original columns from predicted data: %s'%e)

        results_proba = None
        proba_classes = None
        results = None
        if threshold is not None:
            results_proba = fitted_model.predict_proba(predict_data)
            proba_classes = list(fitted_model.classes_)
        else:
            results = fitted_model.predict(predict_data)

        target_categoricals = fsclient.read_json_file(os.path.join(
                self.ctx.config.get_model_path(model_id), "target_categoricals.json"))
        target_categories = target_categoricals.get(self.ctx.config.get('target'), {}).get("categories")

        return results, results_proba, proba_classes, target_categories, model_features

    @error_handler
    @authenticated
    def undeploy(self, model_id, locally):
        if not self.ctx.config.get('undeploy/service_only'):
            model_path = self.ctx.config.get_model_path(model_id)
            self.ctx.log("Undeploy model. Remove model folder: %s"%model_path)
            fsclient.remove_folder(model_path)

        if not locally:
            from azureml.train.automl.run import AutoMLRun
            from azureml.core.webservice import Webservice
            from azureml.exceptions import WebserviceException

            ws, experiment = self._get_experiment()
            model_run = AutoMLRun(experiment = experiment, run_id = model_id)
            model_name = model_run.properties['model_name']

            service_name = self._deploy_service_name(model_name)
            try:
                Webservice(ws, service_name).delete()
            except WebserviceException as exc:
                #self.ctx.log(exc.message)
                raise AzureException(exc.message)

            self.ctx.log("Model endpoint has been removed.")

    @error_handler
    @authenticated
    def review_alert(self, model_id, parameters):
        raise AzureException("Not Implemented. Set use_auger_cloud: True in config.yml")

    @error_handler
    @authenticated
    def review(self, model_id):
        raise Exception("Not Implemented. Set use_auger_cloud: True in config.yml")
