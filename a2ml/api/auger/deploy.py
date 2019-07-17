import os
import subprocess

from a2ml.api.auger.base import AugerBase
from auger.api.cloud.cluster import AugerClusterApi
from auger.api.cloud.pipeline import AugerPipelineApi
from auger.api.cloud.utils.exception import AugerException
from auger.api.cloud.pipeline_file import AugerPipelineFileApi


class AugerDeploy(AugerBase):
    """Deploy you Model on Auger."""

    def __init__(self, ctx):
        super(AugerDeploy, self).__init__(ctx)

    @AugerBase._error_handler
    def deploy(self, model_id, locally=False):
        # verify avalability of auger credentials
        self.credentials.verify()

        if locally:
            self.depoly_model_locally(model_id)
        else:
            self.deploy_model_on_cloud(model_id)

    def deploy_model_on_cloud(self, model_id):
        self.ctx.log('Deploying model %s' % model_id)

        self.start_project()
        pipeline_properties = AugerPipelineApi(
            self.ctx, None).create(model_id)

        self.ctx.log('Deployed Auger model: %s' %
            pipeline_properties.get('id'))

    def depoly_model_locally(self, model_id):
        is_loaded, model_path, model_name = self.verify_local_model(model_id)

        if not is_loaded:
            self.ctx.log('Downloading model %s' % model_id)

            self.start_project()
            pipeline_file_api = AugerPipelineFileApi(self.ctx, None)
            pipeline_file_properties = pipeline_file_api.create(model_id)
            downloaded_model_file = pipeline_file_api.download(
                pipeline_file_properties['signed_s3_model_path'],
                model_path, model_id)

            self.ctx.log('Downloaded model to %s' % downloaded_model_file)
        else:
            self.ctx.log('Downloaded model is %s' % model_name)

        self.ctx.log('Pulling docker image required to predict')
        self._docker_pull_image()

    @staticmethod
    def verify_local_model(model_id):
        model_path = os.path.abspath(
            os.path.join(os.getcwd(), 'models'))
        model_name = '%s/model-%s.zip' % (model_path, model_id)
        return os.path.isfile(model_name), model_path, model_name

    def _docker_pull_image(self):
        cluster_settings = AugerClusterApi.get_cluster_settings(self.ctx)
        docker_tag = cluster_settings.get('kubernetes_stack')

        try:
            subprocess.check_call(
                'docker pull deeplearninc/auger-ml-worker:%s' % \
                 docker_tag, shell=True)
        except subprocess.CalledProcessError as e:
            raise AugerException('Can\'t pull Docker container...')

        return docker_tag
