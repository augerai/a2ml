from .base import AugerBaseApi


class AugerActualApi(AugerBaseApi):
    """Auger Trial API."""

    def __init__(self, ctx, pipeline_api, prediction_id=None):
        super(AugerActualApi, self).__init__(
            ctx, pipeline_api, prediction_id)

    def create(self, records):
        return self._call_create(params={
            'pipeline_id': self.parent_api.object_id,
            'actuals': records}, has_return_object=False)
