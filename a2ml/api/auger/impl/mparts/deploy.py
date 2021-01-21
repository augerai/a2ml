import os
import subprocess
import numpy as np

from ..cloud.cluster import AugerClusterApi
from ..cloud.pipeline import AugerPipelineApi
from ..cloud.experiment_session import AugerExperimentSessionApi
from ..cloud.endpoint import AugerEndpointApi
from ..cloud.review_alert import AugerReviewAlertApi
from ..cloud.review_alert_item import AugerReviewAlertItemApi
from ..exceptions import AugerException
from ..cloud.pipeline_file import AugerPipelineFileApi
from a2ml.api.utils import fsclient


class ModelDeploy(object):
    """Deploy Model on locally or on Auger Cloud."""

    def __init__(self, ctx, project):
        super(ModelDeploy, self).__init__()
        self.project = project
        self.ctx = ctx

    def execute(self, model_id, locally=False, review=True, name=None, algorithm=None, score=None):
        if locally:
            return self.deploy_model_locally(model_id, review, name)
        else:
            return self.deploy_model_in_cloud(model_id, review, name, algorithm, score)

    def create_update_review_alert(self, model_id, pipeline_properties=None, parameters=None, name=None):
        if not self.ctx.config.get('review'):
            raise Exception("To use Review, please add section review to config.yml")

        if not pipeline_properties:
            pipeline_properties = AugerPipelineApi(self.ctx, None, model_id).properties()

        endpoint_api = None    
        if not pipeline_properties.get('endpoint_pipelines'):
            self.ctx.log('Creating review endpoint ...')
            endpoint_api = AugerEndpointApi(self.ctx, None)
            if not name:
                name = fsclient.get_path_base_name(self.ctx.config.get('source'))
            endpoint_properties = endpoint_api.create(pipeline_properties.get('id'), name)
            pipeline_properties['endpoint_pipelines'] = [endpoint_properties.get('id')]

        if pipeline_properties.get('endpoint_pipelines'):
            if endpoint_api is None:
                endpoint_api = AugerEndpointApi(self.ctx, None, 
                    pipeline_properties['endpoint_pipelines'][0].get('endpoint_id'))

            session_id = endpoint_api.properties().get('primary_experiment_session_id')
            if session_id:
                AugerExperimentSessionApi(self.ctx, None, None, session_id).update_settings()

            AugerReviewAlertApi(self.ctx, endpoint_api).create_update(parameters)
        else:
            self.ctx.log('Model is not belong to any review endpoint. Skipping ...')

    def review(self, model_id):
        pipeline_properties = AugerPipelineApi(self.ctx, None, model_id).properties()
        result = {}
        if not pipeline_properties.get('endpoint_pipelines'):
            return result

        endpoint_api = AugerEndpointApi(self.ctx, None, 
            pipeline_properties['endpoint_pipelines'][0].get('endpoint_id'))

        alert_items = AugerReviewAlertItemApi(self.ctx, endpoint_api).list()
        if not alert_items:
            return result

        alert_items = sorted(alert_items, key=lambda k: k['id'], reverse=True)
        alert_item = alert_items[0]
        error_states = ['review_data_build_failed', 'project_file_processing_failed', 'experiment_session_failed', 'pipeline_creating_failed']

        alert = AugerReviewAlertApi(self.ctx, None, alert_item['review_alert_id']).properties()
        status = "started"
        error = ""

        if alert.get('actions') == 'retrain_deploy':
            retrain_status = alert_item.get('action_results', {}).get('retrain')
            if retrain_status in error_states:
                status = 'error'
                error = retrain_status
            else:
                if retrain_status == 'external_pipeline_should_be_rebuilt':
                    status = 'retrain'
                else:    
                    redeploy_status = alert_item.get('action_results', {}).get('redeploy')
                    if redeploy_status in error_states:
                        status = 'error'
                        error = redeploy_status
                    elif redeploy_status == 'endpoint_updated' or redeploy_status == 'endpoint_has_better_pipeline':
                        status = 'completed'
        elif alert.get('actions') == 'retrain':
            retrain_status = alert_item.get('action_results', {}).get('retrain')
            if retrain_status in error_states:
                status = 'error'
                error = retrain_status
            elif retrain_status == 'experiment_session_done':
                status = 'completed'
            elif retrain_status == 'external_pipeline_should_be_rebuilt':
                status = 'retrain'
        else:
            status = 'completed'

        accuracy = 0
        if alert_item.get('values'):
            accuracy = np.mean(alert_item['values'])
        result = {
            'status': status,
            'error': error,
            'accuracy': accuracy
        }
        return result
            
    def deploy_model_in_cloud(self, model_id, review, name, algorithm, score):
        self.ctx.log('Deploying model %s' % model_id)

        if self.ctx.is_external_provider():
            pipeline_properties = AugerPipelineApi(
                self.ctx, None).create_external(review, name, self.project.object_id, algorithm, score)
        else:    
            self.project.start()
            pipeline_properties = AugerPipelineApi(
                self.ctx, None).create(model_id, review, name)

        if pipeline_properties.get('status') == 'ready':
            if review:
                self.create_update_review_alert(model_id, pipeline_properties, name=name)

            self.ctx.log('Deployed Model on Auger Cloud. Model id is %s' % \
                pipeline_properties.get('id'))            
        else:
            self.ctx.log('Deployed Model on Auger Cloud failed. Model id is %s.Error: %s' % \
                (pipeline_properties.get('id'), pipeline_properties.get('error_message', "")))

        return pipeline_properties.get('id')

    def deploy_model_locally(self, model_id, review, name):
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
        is_exists = fsclient.is_folder_exists(os.path.join(model_path,"model-%s"%model_id))
        if not is_exists:
            is_exists = fsclient.is_file_exists(model_name)
        return is_exists, model_path, model_name

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
