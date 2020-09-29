from .base import AugerBaseApi
from ..exceptions import AugerException


class AugerReviewAlertApi(AugerBaseApi):
    """Auger Review Alert API."""

    def __init__(self, ctx, endpoint_api, alert_id=None):
        super(AugerReviewAlertApi, self).__init__(ctx, endpoint_api, None, alert_id)

    def create(self, params):
        return self._call_create(params)
