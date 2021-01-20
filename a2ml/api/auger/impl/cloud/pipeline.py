from .base import AugerBaseApi
from .prediction import AugerPredictionApi
from .actual import AugerActualApi
from ..exceptions import AugerException


class AugerPipelineApi(AugerBaseApi):
    """Auger Pipeline API."""

    def __init__(self, ctx, experiment_api, pipeline_id=None):
        super(AugerPipelineApi, self).__init__(
            ctx, experiment_api, None, pipeline_id)

    def create(self, trial_id, review=True, name=None):
        return self._call_create({'trial_id': trial_id, 'is_review_model_enabled' : review, 'name': name},
            ['creating_files', 'packaging', 'deploying'])

    def create_external(self, review, name, project_id, algorithm, score):
        return self._call_create({'name': name, 'is_review_model_enabled' : review, 
                'project_id': project_id, 
                'target_column': self.ctx.config.get('target'), 
                'score_name': self.ctx.config.get('experiment/metric'), 
                'task_type': self.ctx.config.get('model_type'),
                'algorithm_name': algorithm,
                'score_value': score,
                'binary_classification': self.ctx.config.get('binary_classification')
            },
            ['creating_files', 'packaging', 'deploying'])            

    def remove(self, trial_id):
        try:
            return self._call_update({'id': trial_id, 'status': 'undeploying'}, progress=['ready','packaged_with_error'])
        except Exception as e:
            if "transition to this status impossible" in str(e):
                self.ctx.log("Model %s already undeployed."%trial_id)
            else:
                self.ctx.error("Model %s undeploy error: %s"%(trial_id,e))

    def check_endpoint(self, props=None):
        if not props:
            props = self.properties()

        is_endpoint = False    
        if props.get('is_review_model_enabled') and props.get('endpoint_pipelines'):
            self.object_id = props['endpoint_pipelines'][0].get('endpoint_id')
            self._set_api_request_path("AugerEndpointApi")
            is_endpoint = True

        return is_endpoint

    def predict(self, records, features, threshold=None, file_url=None, predicted_at=None):
        if self.object_id is None:
            raise AugerException('Please provide Auger Pipeline id')

        props = self.properties()
        if not self.check_endpoint(props):
            status = props.get('status')
            if status != 'ready':
                if 'error' in status:
                    # there are following options currently:
                    # [created_files_with_error, packaged_with_error,
                    # deployed_with_error undeployed_with_error]
                    error_message = props.get('error_message')
                    raise AugerException(
                        """Pipeline %s deployment has failed with following """
                        """error on Auger Cloud: `%s`""" % (
                            self.object_id, error_message))
                else:
                    raise AugerException(
                        "Pipeline %s is not ready..." % self.object_id)

        prediction_api = AugerPredictionApi(self.ctx, self, use_endpoint=self.check_endpoint(props))
        prediction_properties = \
            prediction_api.create(records, features, threshold=threshold, file_url=file_url, predicted_at=predicted_at)
        return prediction_properties.get('result')

    def actual(self, records, features, actuals_at, actuals_path, actual_date_column):
        if self.object_id is None:
            raise AugerException('Please provide Auger Pipeline id')

        actual_api = AugerActualApi(self.ctx, self, use_endpoint=self.check_endpoint())
        actual_api.create(records, features, actuals_at, actuals_path, actual_date_column)

        #TODO: get object actual from cloud
        return True

    def delete_actuals(self, with_predictions, begin_date, end_date):
        if self.object_id is None:
            raise AugerException('Please provide Auger Pipeline id')

        actual_api = AugerActualApi(self.ctx, self, use_endpoint=self.check_endpoint())
        return actual_api.delete(with_predictions, begin_date, end_date)
