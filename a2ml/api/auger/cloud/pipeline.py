from .base import AugerBaseApi
from .prediction import AugerPredictionApi
from .utils.exception import AugerException


class AugerPipelineApi(AugerBaseApi):
    """Auger Pipeline API."""

    def __init__(self, ctx, experiment_api, pipeline_id=None):
        super(AugerPipelineApi, self).__init__(
            ctx, experiment_api, None, pipeline_id)

    def create(self, trial_id):
        return self._call_create({'trial_id': trial_id},
            ['creating_files', 'packaging', 'deploying'])

    def predict(self, records, features, threshold=None):
        if self.object_id is None:
            raise AugerException('Please provide Auger Pipeline id')

        if self.properties().get('status') != 'ready':
            raise AugerException(
                "Pipeline %s is not ready or has issues..." % self.object_id)

        prediction_api = AugerPredictionApi(self.ctx, self)
        prediction_properties = \
            prediction_api.create(records, features, threshold)

        return prediction_properties.get('result')
