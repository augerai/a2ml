import re
import sys

from auger.hub_api_client import HubApiClient
from ..exceptions import AugerException


REQUEST_LIMIT = 100

class RestApi(object):
    """Warapper around Auger Cloud Rest Api."""

    def __init__(self, url, token, debug=False):
        super(RestApi, self).__init__()
        self.hub_client = HubApiClient(hub_app_url=url, token=token, debug=debug)
        self.api_url = url
        self.debug = debug

    def get_status(self, obj, obj_id):
        return self.hub_client.get_status(object=obj, id=obj_id)

    def call_ex(self, method, params={}):
        params = params.copy()

        if params.get('id') and not method.startswith('create_'):
            oid = params['id']
            del params['id']
            return getattr(self.hub_client, method)(oid, **params)
        else:
            return getattr(self.hub_client, method)(**params)

    def call(self, method, params={}):
        result = self.call_ex(method, params)

        if 'data' in result:
            return result['data']

        raise AugerException("Call of Auger API method %s failed." % method)

    def request_list(self, record_type, params):
        offset = params.get('offset', 0)
        limit = params.get('limit', REQUEST_LIMIT)
        p = params.copy()
        while limit > 0:
            p['offset'] = offset
            p['limit'] = limit
            response = self.call_ex('get_' + record_type, p)
            try:
                if not 'data' in response or not 'meta' in response:
                    raise AugerException("Read list of %s failed." % record_type)

                for item in response['data']:
                    yield item

                received = len(response['data'])
                offset += received
                limit -= received
                if offset >= response['meta']['pagination']['total']:
                    break
            except Exception as e:
                    import traceback; traceback.print_exc()
