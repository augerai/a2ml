from .base import AugerBaseApi
from ..exceptions import AugerException


class AugerPredictionApi(AugerBaseApi):
    """Auger Trial API."""

    def __init__(self, ctx, pipeline_api, use_endpoint=False):
        super(AugerPredictionApi, self).__init__(ctx, pipeline_api)
        assert pipeline_api is not None, 'Pipeline must be set for Prediction'

        self.use_endpoint = use_endpoint
        if self.use_endpoint:
            self.parent_id_name = "endpoint_id"
            self._set_api_request_path("AugerEndpointPredictionApi")

    def create(self, records, features, threshold=None, file_url=None, predicted_at=None, 
        no_features_in_result=None, score=False, score_true_data=None):
        params = {
            'records': records, 
            'features': features,
            'threshold': threshold
        }
        if self.use_endpoint:
            params['endpoint_id'] = self.parent_api.object_id
            if not self.ctx.config.get('support_model_history'):
                params['primary_only'] = True
        else:
            params['pipeline_id'] = self.parent_api.object_id

        if file_url:
            params['file_url'] = file_url
                
        if predicted_at:
            params['predicted_at'] = str(predicted_at)

        if no_features_in_result is not None:
            params['no_features_in_result'] = no_features_in_result

        if score:
            params['score'] = score

        if score_true_data:
            params['score_true_data'] = score_true_data

        return self._call_create(params, ['requested', 'running'])
