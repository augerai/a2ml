from a2ml.api.auger.hub.hub_api import HubApi
from a2ml.api.auger.hub.hub_api import REQUEST_LIMIT


class AugerOrgApi(object):
    """Wrapper around HubApi for Auger Organization."""
    def __init__(self, hub_client, name):
        super(AugerOrgApi, self).__init__()
        self.name  = name
        self.hub_client = hub_client

    def properties(self):
        orgs_list = self.hub_client.call_hub_api(
            'get_organizations', {
                'name': self.name,
                'limit': REQUEST_LIMIT})

        alt_org_name = self.name.replace('_', '-')

        if len(orgs_list) > 0:
            for item in orgs_list:
                if item['name'] == self.name:
                    return item

                if item['name'] == alt_org_name:
                    return item

        return None
