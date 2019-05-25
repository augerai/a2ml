from a2ml.api.auger.hub.base import AugerBaseApi


class AugerOrganizationApi(AugerBaseApi):
    """Wrapper around HubApi for Auger Organization."""

    def __init__(self, hub_client, org_name=None, org_id=None):
        super(AugerOrganizationApi, self).__init__(
            hub_client, None, org_name, org_id)

    def get_cluster_mode(self):
        cluster_mode = getattr(self, 'cluster_mode', None)
        if not cluster_mode:
            self.cluster_mode = self.properties().get('cluster_mode')
        return self.cluster_mode
