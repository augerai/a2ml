from .base import AugerBaseApi
from ..exceptions import AugerException


class AugerEndpointApi(AugerBaseApi):
    """Auger Endpoint API."""

    def __init__(self, ctx, experiment_api, endpoint_id=None):
        super(AugerEndpointApi, self).__init__(
            ctx, experiment_api, None, endpoint_id)

    def create(self, pipeline_id):
        return self._call_create({'pipeline_id': pipeline_id},[])
