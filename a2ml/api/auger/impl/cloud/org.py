from .base import AugerBaseApi
from ..exceptions import AugerException


class AugerOrganizationApi(AugerBaseApi):
    """Auger Organization API."""

    def __init__(self, ctx, org_name=None, org_id=None):
        super(AugerOrganizationApi, self).__init__(
            ctx, None, org_name, org_id)

    def get_cluster_mode(self):
        cluster_mode = getattr(self, 'cluster_mode', None)
        if not cluster_mode:
            self.cluster_mode = self.properties().get('cluster_mode')
        return self.cluster_mode

    def create(self):
        raise AugerException(
            'You could\'t create organization using Auger Cloud API.'
            ' Please use Auger UI to do that...')

    def delete(self):
        raise AugerException(
            'You could\'t delete organization using Auger Cloud API.'
            ' Please use Auger UI to do that...')
