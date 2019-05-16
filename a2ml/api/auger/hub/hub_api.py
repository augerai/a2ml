import sys

from auger.hub_api_client import HubApiClient


class HubApi(object):
    """Auger Hub Api call wrapper."""
    def __init__(self, url, token):
        super(HubApi, self).__init__()
        self.hub_client = HubApiClient(hub_app_url=url,token=token)

    def call_hub_api_ex(self, method, params={}):
        params = params.copy()

        if params.get('id') and not method.startswith('create_'):
            id = params['id']
            del params['id']
            return getattr(self.hub_client, method)(id, **params)
        else:
            return getattr(self.hub_client, method)(**params)

    def call_hub_api(self, method, params={}):
        result = self.call_hub_api_ex(method, params)

        if 'data' in result:
            return result['data']

        raise Exception("Call of HUB API method %s failed." % keys)
