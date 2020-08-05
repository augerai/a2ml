import os
import subprocess

from ..cloud.cluster import AugerClusterApi
from ..cloud.pipeline import AugerPipelineApi
from ..exceptions import AugerException
from ..cloud.pipeline_file import AugerPipelineFileApi
from a2ml.api.utils import fsclient

class ModelDeploy(object):
    """Deploy Model on locally or on Auger Cloud."""

    def __init__(self, ctx, project):
        super(ModelDeploy, self).__init__()
        self.project = project
        self.ctx = ctx

    def execute(self, model_id, locally=False, review=True):
        if locally:
            return self.deploy_model_locally(model_id, review)
        else:
            return self.deploy_model_in_cloud(model_id, review)

    def deploy_model_in_cloud(self, model_id, review):
        self.ctx.log('Deploying model %s' % model_id)

        self.project.start()

        pipeline_properties = AugerPipelineApi(
            self.ctx, None).create(model_id, review)

        self.ctx.log('Deployed Model on Auger Cloud. Model id is %s' % \
            pipeline_properties.get('id'))

        return pipeline_properties.get('id')

    def deploy_model_locally(self, model_id, review):
        is_loaded, model_path, model_name = self.verify_local_model(model_id)
        #TODO: support review flag
        if not is_loaded:
            self.ctx.log('Downloading model %s' % model_id)

            self.project.start()

            pipeline_file_api = AugerPipelineFileApi(self.ctx, None)
            pipeline_file_properties = pipeline_file_api.create(model_id)
            downloaded_model_file = pipeline_file_api.download(
                pipeline_file_properties['signed_s3_model_path'],
                model_path, model_id)

            self.ctx.log('Downloaded model to %s' % downloaded_model_file)

            self.ctx.log('Pulling docker image required to predict')
            self._docker_pull_image()            
        else:
            self.ctx.log('Downloaded model is %s' % model_name)

        return model_id

    def verify_local_model(self, model_id):
        model_path = os.path.join(self.ctx.config.get_path(), 'models')
        model_name = os.path.join(model_path, 'model-%s.zip' % model_id)
        return fsclient.is_file_exists(model_name), model_path, model_name

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
