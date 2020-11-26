from .base import AugerBaseApi
from ..exceptions import AugerException
from .review_alert_item import AugerReviewAlertItemApi
from .review_alert import AugerReviewAlertApi


class AugerEndpointApi(AugerBaseApi):
    """Auger Endpoint API."""

    def __init__(self, ctx, endpoint_api, endpoint_id=None):
        super(AugerEndpointApi, self).__init__(
            ctx, endpoint_api, None, endpoint_id)

    def create(self, pipeline_id, name):
        return self._call_create({'pipeline_id': pipeline_id, 'name': name},[])
