from .base import AugerBaseApi
from ..exceptions import AugerException
from .review_alert_item import AugerReviewAlertItemApi
from .review_alert import AugerReviewAlertApi


class AugerEndpointPipelineApi(AugerBaseApi):
    """Auger Endpoint Pipeline API."""

    def __init__(self, ctx, object_id):
        super(AugerEndpointPipelineApi, self).__init__(
            ctx, None, None, object_id)
