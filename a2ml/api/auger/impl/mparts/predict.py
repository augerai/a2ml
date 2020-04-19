import os
import shutil
import subprocess
from zipfile import ZipFile

from .deploy import ModelDeploy
from ..cloud.cluster import AugerClusterApi
from ..cloud.pipeline import AugerPipelineApi
from ..exceptions import AugerException
from a2ml.api.utils.dataframe import DataFrame


class ModelPredict():
    """Predict using deployed Auger Model."""

    def __init__(self, ctx):
        super(ModelPredict, self).__init__()
        self.ctx = ctx

    def execute(self, filename, model_id, threshold=None, locally=False):
        self.ctx.log('Predicting on data in %s' % filename)
        filename = os.path.abspath(filename)

        if locally:
            predicted = self._predict_locally(filename, model_id, threshold)
        else:
            predicted = self._predict_on_cloud(filename, model_id, threshold)

        self.ctx.log('Predictions stored in %s' % predicted)

        return predicted

    def _predict_on_cloud(self, filename, model_id, threshold=None):
        target = self.ctx.config.get('target', None)
        records, features = DataFrame.load_records(filename, target)

        pipeline_api = AugerPipelineApi(self.ctx, None, model_id)
        predictions = pipeline_api.predict(
            records, features, threshold)

        predicted = os.path.splitext(filename)[0] + "_predicted.csv"
        DataFrame.save(predicted, predictions)

        return predicted

    def _predict_locally(self, filename, model_id, threshold):
        is_model_loaded, model_path, model_name = \
            ModelDeploy.verify_local_model(model_id)

        if not is_model_loaded:
            raise AugerException('Model isn\'t loaded locally. '
                'Please use a2ml deploy command to download model.')

        model_path, model_existed = self._extract_model(model_name)

        try:
            predicted = \
                self._docker_run_predict(filename, threshold, model_path)
        finally:
            # clean up unzipped model
            # if it wasn't unzipped before
            if not model_existed:
                shutil.rmtree(model_path, ignore_errors=True)

        return predicted

    def _extract_model(self, model_name):
        model_path = os.path.splitext(model_name)[0]
        model_existed = os.path.exists(model_path)

        if not model_existed:
            with ZipFile(model_name, 'r') as zip_file:
                zip_file.extractall(model_path)

        return model_path, model_existed

    def _docker_run_predict(self, filename, threshold, model_path):
        cluster_settings = AugerClusterApi.get_cluster_settings(self.ctx)
        docker_tag = cluster_settings.get('kubernetes_stack')
        result_file = os.path.basename(filename)
        data_path = os.path.dirname(filename)

        call_args = "--path_to_predict=./model_data/%s %s" % \
            (result_file, "--threshold=%s" % str(threshold) if threshold else '')

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
            getattr(subprocess,
                'check_call' if self.ctx.debug else 'check_output')(
                command, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            raise AugerException('Error running Docker container...')

        return os.path.join(data_path,
            os.path.splitext(result_file)[0] + "_predicted.csv")
