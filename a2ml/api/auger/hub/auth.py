from a2ml.api.auger.hub.hub_api import HubApi

class AugerAuthApi(object):
    """Wrapper around HubApi for Authentication."""
    def __init__(self):
        super(AugerAuthApi, self).__init__()

    def login(self, ctx, username, password, url):
        hub_api = HubApi().setup(ctx, url, None)
        hub_api.call_hub_api_ex(
            'create_token', {'email': username, 'password': password})
        hub_api.setup(ctx, url, res['data']['token'])
        return res['data']['token']
