from .base import AugerBaseApi


class AugerActualApi(AugerBaseApi):
    """Auger Trial API."""

    def __init__(self, ctx, pipeline_api, prediction_id=None):
        super(AugerActualApi, self).__init__(
            ctx, pipeline_api, prediction_id)

    def create(self, records, actuals_at, actuals_path=None):
        params = {
            'pipeline_id': self.parent_api.object_id,
        }

        if records:
            params['actuals'] = records

        if actuals_path:
            params['actuals_path'] = actuals_path

        if actuals_at:
            params['actuals_at'] = str(actuals_at)

        return self._call_create(
            params=params, 
            has_return_object=False)

    def delete(self, with_predictions, begin_date, end_date):
        return self.rest_api.call( 'delete_%ss' % self.api_request_path, {
                'pipeline_id': self.parent_api.object_id,
                'with_predictions': with_predictions,
                'from': begin_date,
                'to': end_date
            })
