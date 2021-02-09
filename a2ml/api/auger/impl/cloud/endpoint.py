from .base import AugerBaseApi
from ..exceptions import AugerException
from .review_alert_item import AugerReviewAlertItemApi
from .review_alert import AugerReviewAlertApi
from .cluster_task import AugerClusterTaskApi

class AugerEndpointApi(AugerBaseApi):
    """Auger Endpoint API."""

    def __init__(self, ctx, endpoint_api, endpoint_id=None):
        super(AugerEndpointApi, self).__init__(
            ctx, endpoint_api, None, endpoint_id)

    def create(self, pipeline_id, name):
        return self._call_create({'pipeline_id': pipeline_id, 'name': name},[])

    def update_roi(self):
        roi_names = ['review/roi/filter', 'review/roi/investment', 'review/roi/revenue']
        roi_values = []
        roi_exists = False
        for name in roi_names:
            if self.ctx.config.get(name):
                roi_exists = True

            roi_values.append(self.ctx.config.get(name))

        if roi_exists:
            res = self.rest_api.hub_client.create_endpoint_roi_validation(
                endpoint_id=self.object_id,
                expressions=roi_values,
            )
            cluster_task = AugerClusterTaskApi(self.ctx, cluster_task_id=res['data']['id'])
            cluster_task.wait_for_status(['pending', 'received', 'started', 'retry'])
            props = cluster_task.properties()
            isValid = True
            for idx, item in enumerate(props.get('result', [])):
                if not item.get('is_valid'):
                    isValid = False
                    self.ctx.error("Review ROI config parameter '%s' = '%s' is invalid. Error: %s"%(
                        roi_names[idx], roi_values[idx], item.get('error')))                    

            if isValid:
                return self._call_update({ 'id': self.object_id, 
                    'roi_filter': roi_values[0], 'roi_investment': roi_values[1], 'roi_revenue': roi_values[2],
                })