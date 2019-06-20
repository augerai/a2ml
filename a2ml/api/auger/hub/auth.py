from a2ml.api.auger.hub.rest_api import RestApi
from a2ml.api.auger.hub.org import AugerOrganizationApi
from a2ml.api.auger.hub.utils.exception import AugerException


class AugerAuthApi(object):
    """Auger Authentication API."""
    def __init__(self):
        super(AugerAuthApi, self).__init__()

    def login(self, ctx, username, password, organisation, url):
        rest_api = RestApi().setup(ctx, url, None)
        res = rest_api.call_ex(
            'create_token', {'email': username, 'password': password})
        rest_api.setup(ctx, url, res['data']['token'])
        org_api = AugerOrganizationApi(organisation)
        if org_api.properties() == None:
            raise AugerException(
                'Auger Organization %s doesn\'t exist' % organisation)
        return res['data']['token']
