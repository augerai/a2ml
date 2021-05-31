import os
import shutil
import subprocess
import sys
import pandas as pd

from .deploy import ModelDeploy
from ..cloud.cluster import AugerClusterApi
from ..cloud.pipeline import AugerPipelineApi
from ..exceptions import AugerException
from a2ml.api.utils import fsclient, getsizeof_deep
from a2ml.api.utils.dataframe import DataFrame
from a2ml.api.model_review.model_helper import ModelHelper
from ..decorators import with_project
from ..project import Project


class ModelPredict():
    """Predict using deployed Auger Model."""

    def __init__(self, ctx):
        super(ModelPredict, self).__init__()
        self.ctx = ctx

    def execute(self, filename, model_id, threshold=None, locally=False, data=None, columns=None, 
            predicted_at=None, output=None, no_features_in_result=None):
        if filename and not (filename.startswith("http:") or filename.startswith("https:")) and\
            not fsclient.is_s3_path(filename):
            self.ctx.log('Predicting on data in %s' % filename)
            filename = os.path.abspath(filename)

        if locally:
            if locally == "docker":
                predicted = self._predict_locally_in_docker(filename, model_id, threshold, data, columns, predicted_at, output, no_features_in_result)
            else:
                predicted = self._predict_locally(filename, model_id, threshold, data, columns, predicted_at, output, no_features_in_result)
        else:
            predicted = self._predict_on_cloud(filename, model_id, threshold, data, columns, predicted_at, output, no_features_in_result)

        return predicted

    @with_project(autocreate=False)
    def _upload_file_to_cloud(self, project, filename):
        from ..dataset import DataSet

        file_url, file_name = DataSet(self.ctx, project).upload_file(filename)
        return file_url

    def _process_input(self, filename, data, columns):
        send_records = False
        file_url = None
        records = None
        features = None
        max_records_size = 10*1024

        if filename:
            if not (filename.startswith("http:") or filename.startswith("https:")) and \
               not fsclient.is_s3_path(filename):
                file_size = fsclient.get_file_size(filename)
                if file_size <= max_records_size:
                    self.ctx.log("Local file '%s' with size %s(KB) is smaller %s KB, so send records to hub." % (filename, file_size/1024, max_records_size/1024))
                    send_records = True
            else:
                file_url = filename
                if fsclient.is_s3_path(file_url):
                    with fsclient.with_s3_downloaded_or_local_file(file_url) as local_path:
                        file_url = self._upload_file_to_cloud(local_path)
        elif data is not None and isinstance(data, pd.DataFrame):
            if len(data) < 100:
                send_records = True
        else:
            size = getsizeof_deep(data)
            if size is None or size > max_records_size:
                self.ctx.log("Size of data %.2f KB > %.2f KB, so send file to hub." % (size/1024, max_records_size/1024))
            else:
                send_records = True

        if send_records:
            ds = DataFrame.create_dataframe(filename, data, columns)
            records = ds.get_records()
            features = ds.columns
        else:
            if not file_url:
                if not filename:
                    with fsclient.save_atomic("temp_predict.csv.gz", move_file=False) as local_path:
                        ds = DataFrame.create_dataframe(filename, data, columns)
                        ds.saveToCsvFile(local_path)
                        file_url = self._upload_file_to_cloud(local_path)
                else:
                    file_url = self._upload_file_to_cloud(filename)

        return records, features, file_url, data is not None and isinstance(data, pd.DataFrame)

    def _check_model_project(self, pipeline_api):
        model_project_name = Project(self.ctx, project_id=pipeline_api.properties().get('project_id')).properties().get('name')

        if model_project_name != self.ctx.config.get('name'):
            raise AugerException("Project name: %s in config.yml is different from model project name: %s. Please change name in config.yml."%(
                self.ctx.config.get('name'), model_project_name))

    def _predict_on_cloud(self, filename, model_id, threshold, data, columns, predicted_at, output, no_features_in_result):
        records, features, file_url, is_pandas_df = self._process_input(filename, data, columns)
        temp_file = None
        ds_result = None
        if records is not None and len(records) == 0:
            ds_result =  DataFrame.create_dataframe(None, [], features+[self.ctx.config.get('target')])
        else:
            pipeline_api = AugerPipelineApi(self.ctx, None, model_id)
            predictions = pipeline_api.predict(records, features, threshold=threshold, file_url=file_url, 
                predicted_at=predicted_at, no_features_in_result=no_features_in_result)

            try:
                ds_result = DataFrame.create_dataframe(predictions.get('signed_prediction_url'),
                    records=predictions.get('data'), features=predictions.get('columns'))
            except Exception as e:
                self._check_model_project(pipeline_api)

                msg = "Prediction result file(%s) cannot be downloaded."%predictions.get('signed_prediction_url')
                raise AugerException(msg+"Please contact support.")

            temp_file = ds_result.options['data_path'] if predictions.get('signed_prediction_url') else None

        try:
            ds_result.options['data_path'] = filename
            ds_result.loaded_columns = columns
            ds_result.from_pandas = is_pandas_df

            # Save prediction in local model folder if exist
            is_model_loaded, model_path = ModelDeploy(self.ctx, None).verify_local_model(model_id)
            if not is_model_loaded:
                model_path = None

            return ModelHelper.save_prediction(ds_result,
                prediction_id = None, json_result=False, count_in_result=False, prediction_date=predicted_at,
                model_path=model_path, model_id=model_id, output=output)
        finally:
            if temp_file:
                fsclient.remove_file(temp_file)

    def _predict_locally(self, filename_arg, model_id, threshold, data, columns, predicted_at, output, no_features_in_result):
        from auger_ml.model_exporter import ModelExporter

        is_model_loaded, model_path = ModelDeploy(self.ctx, None).verify_local_model(model_id)
        if not is_model_loaded:
            raise AugerException('Model isn\'t loaded locally. '
                'Please use a2ml deploy command to download model.')

        if columns is not None:
            columns = list(columns)

        res, options = ModelExporter({}).predict_by_model_to_ds(model_path, 
            path_to_predict=filename_arg, records=data, features=columns, 
            threshold=threshold, no_features_in_result=no_features_in_result)

        ds_result = DataFrame({'data_path': None})
        ds_result.df = res.df
        ds_result.loaded_columns = columns
        if isinstance(data, pd.DataFrame):
            ds_result.from_pandas = True

        return ModelHelper.save_prediction(ds_result,
            prediction_id = None, json_result=False, count_in_result=False, prediction_date=predicted_at,
            model_path=model_path, model_id=model_id, output=output)

        # return ModelExporter({}).predict_by_model(model_path=model_path,
        #     path_to_predict=filename_arg, records=data, features=columns, 
        #     threshold=threshold, prediction_date=predicted_at, 
        #     no_features_in_result=no_features_in_result) #, output=output)

    def _predict_locally_in_docker(self, filename_arg, model_id, threshold, data, columns, predicted_at, output, no_features_in_result):
        model_deploy = ModelDeploy(self.ctx, None)
        is_model_loaded, model_path = model_deploy.verify_local_model(model_id, add_model_folder=False)
        if not is_model_loaded:
            raise AugerException('Model isn\'t loaded locally. '
                'Please use a2ml deploy command to download model.')

        filename = filename_arg
        if not filename:
            ds = DataFrame.create_dataframe(filename, data, columns)
            filename = os.path.join(self.ctx.config.get_path(), '.augerml', 'predict_data.csv')
            ds.saveToCsvFile(filename, compression=None)

        predicted = self._docker_run_predict(filename, threshold, model_path)

        if not filename_arg:
            ds_result = DataFrame.create_dataframe(predicted)

            ds_result.options['data_path'] = None
            ds_result.loaded_columns = columns

            return ModelHelper.save_prediction(ds_result,
                prediction_id = None,
                json_result=False, count_in_result=False, prediction_date=predicted_at,
                model_path=model_path, model_id=model_id, output=output)
        elif output:
            fsclient.move_file(predicted, output)
            predicted = output

        return predicted

    def _docker_run_predict(self, filename, threshold, model_path):
        cluster_settings = AugerClusterApi.get_cluster_settings(self.ctx)
        docker_tag = cluster_settings.get('kubernetes_stack')
        predict_file = os.path.basename(filename)
        data_path = os.path.abspath(os.path.dirname(filename))
        model_path = os.path.abspath(model_path)

        call_args = "--verbose=True --path_to_predict=./model_data/%s %s" % \
            (predict_file, "--threshold=%s" % str(threshold) if threshold else '')

        command = (r"docker run "
            "-v {model_path}:/var/src/auger-ml-worker/exported_model "
            "-v {data_path}:/var/src/auger-ml-worker/model_data "
            "deeplearninc/auger-ml-worker:{docker_tag} "
            "python ./exported_model/client.py {call_args}").format(
                model_path=model_path, data_path=data_path,
                docker_tag=docker_tag, call_args=call_args)

        try:
            self.ctx.log(
                'Running model in deeplearninc/'
                'auger-ml-worker:%s' % docker_tag)
            result_file = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
            result_file = result_file.decode("utf-8").strip()
            result_file = os.path.basename(result_file)
            # getattr(subprocess,
            #     'check_call' if self.ctx.debug else 'check_output')(
            #     command, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            raise AugerException('Error running Docker container...')

        return os.path.join(data_path, "predictions", result_file)
