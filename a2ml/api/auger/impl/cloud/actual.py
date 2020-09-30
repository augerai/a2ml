from .base import AugerBaseApi
from .cluster_task import AugerClusterTaskApi


class AugerActualApi(AugerBaseApi):
    """Auger Trial API."""

    def __init__(self, ctx, pipeline_api, prediction_id=None, use_endpoint=False):
        super(AugerActualApi, self).__init__(
            ctx, pipeline_api, prediction_id)
        self.use_endpoint = use_endpoint
        if self.use_endpoint:
            self.parent_id_name = "endpoint_id"
            self._set_api_request_path("AugerEndpointActualApi")

    def create(self, records, actuals_at, actuals_path=None):
        params = {}
        if self.use_endpoint:
            params['endpoint_id'] = self.parent_api.object_id
            #params['prediction_group_id'] = 'dffe01f4-39bd-4f7b-832f-61051f8c7e1b'
        else:
            params['pipeline_id'] = self.parent_api.object_id

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
        params = {
            'with_predictions': with_predictions,
            'from': begin_date,
            'to': end_date
        }
        if self.use_endpoint:
            params['endpoint_id'] = self.parent_api.object_id
        else:
            params['pipeline_id'] = self.parent_api.object_id

        res = self.rest_api.call( 'delete_%ss' % self.api_request_path, params)
        if isinstance(res, list):
            res = res[0]
        cluster_task = AugerClusterTaskApi(self.ctx, cluster_task_id=res['id'])
        cluster_task.wait_for_status(['pending', 'received', 'started', 'retry'])

        return True
