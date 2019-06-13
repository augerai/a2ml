from .base import AugerBaseApi


class AugerPredictionApi(AugerBaseApi):
    """Auger Trial API."""

    def __init__(self, ctx, pipeline_api,
        prediction_name=None, prediction_id=None):
        super(AugerPredictionApi, self).__init__(
            ctx, pipeline_api, prediction_name, prediction_id)
        assert pipeline_api is not None, 'Pipeline must be set for Prediction'

    def create(self, records, features, threshold=None):
        return self._call_create({
        'pipeline_id': self.parent_api.object_id,
        'records': records, 'features': features}, ['requested', 'running'])
