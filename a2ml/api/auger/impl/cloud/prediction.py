from .base import AugerBaseApi
from ..exceptions import AugerException


class AugerPredictionApi(AugerBaseApi):
    """Auger Trial API."""

    def __init__(self, ctx, pipeline_api,
        prediction_name=None, prediction_id=None):
        super(AugerPredictionApi, self).__init__(
            ctx, pipeline_api, prediction_name, prediction_id)
        assert pipeline_api is not None, 'Pipeline must be set for Prediction'

    def create(self, records, features, threshold=None, file_url=None, predicted_at=None):
        params = {
            'pipeline_id': self.parent_api.object_id,
            'records': records, 
            'features': features,
            'threshold': threshold
        }
        if file_url:
            params['file_url'] = file_url
                
        if predicted_at:
            params['predicted_at'] = str(predicted_at)

        return self._call_create(params, ['requested', 'running'])
