from a2ml.api.auger.hub.hub_api import HubApi
from a2ml.api.auger.hub.org import AugerOrganizationApi
from a2ml.api.auger.hub.utils.exception import AugerException


class AugerAuthApi(object):
    """Wrapper around HubApi for Authentication."""
    def __init__(self):
        super(AugerAuthApi, self).__init__()

    def login(self, ctx, username, password, organisation, url):
        hub_api = HubApi().setup(ctx, url, None)
        res = hub_api.call_hub_api_ex(
            'create_token', {'email': username, 'password': password})
        hub_api.setup(ctx, url, res['data']['token'])
        org_api = AugerOrganizationApi(organisation)
        if org_api.properties() == None:
            raise AugerException(
                'Auger Organization %s doesn\'t exist' % organisation)
        return res['data']['token']
