from .base import AugerBaseApi
from ..exceptions import AugerException


class AugerReviewAlertItemApi(AugerBaseApi):
    """Auger Review Alert Item API."""

    def __init__(self, ctx, endpoint_api):
        super(AugerReviewAlertItemApi, self).__init__(ctx, endpoint_api)
