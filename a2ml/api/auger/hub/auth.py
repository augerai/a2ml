from a2ml.api.auger.hub.hub_api import HubApi

class AugerAuthApi(object):
    """Wrapper around HubApi for Authentication."""
    def __init__(self):
        super(AugerAuthApi, self).__init__()

    def login(self, username, password, url):
        res = HubApi(url, None).call_hub_api_ex(
            'create_token', {'email': username, 'password': password})
        return res['data']['token']
