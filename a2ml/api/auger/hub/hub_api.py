import re
import sys
import time

from auger.hub_api_client import HubApiClient
from a2ml.api.auger.hub.utils.singleton import Singleton
from a2ml.api.auger.hub.utils.exception import AugerException


REQUEST_LIMIT = 100
STATE_POLL_INTERVAL = 10

class HubApi(Singleton):
    """Auger Cloud Api call wrapper."""

    def __init__(self):
        super(HubApi, self).__init__()

    def setup(self, ctx, url, token):
        self.hub_client = HubApiClient(hub_app_url=url, token=token)
        self.api_url = url
        self.ctx = ctx
        return self

    def get_config(self, name):
        if len(self.ctx.config) == 1:
            return self.ctx.config['auger']
        return self.ctx.config[name]

    def get_status(self, obj, obj_id):
        return self.hub_client.get_status(object=obj, id=obj_id)

    def call_hub_api_ex(self, method, params={}):
        params = params.copy()

        if params.get('id') and not method.startswith('create_'):
            oid = params['id']
            del params['id']
            return getattr(self.hub_client, method)(oid, **params)
        else:
            return getattr(self.hub_client, method)(**params)

    def call_hub_api(self, method, params={}):
        result = self.call_hub_api_ex(method, params)

        if 'data' in result:
            return result['data']

        raise AugerException("Call of HUB API method %s failed." % keys)

    def request_list(self, record_type, params):
        offset = params.get('offset', 0)
        limit = params.get('limit', REQUEST_LIMIT)
        p = params.copy()
        while limit > 0:
            p['offset'] = offset
            p['limit'] = limit
            response = self.call_hub_api_ex('get_' + record_type, p)
            if not 'data' in response or not 'meta' in response:
                raise AugerException("Read list of %s failed." % record_type)

            for item in response['data']:
                yield item

            received = len(response['data'])
            offset += received
            limit -= received
            if offset >= response['meta']['pagination']['total']:
                break

    def wait_for_object_status(self,
        get_status, progress, object_readable_name,
        post_check_status=None, log_status=None):

        def _log_status(obj_status): pass
        log_status  = log_status if log_status else _log_status

        status = get_status()
        last_status = ''

        while status in progress:
            if status != last_status:
                last_status = status
                log_status(status)

            while status == last_status:
                time.sleep(STATE_POLL_INTERVAL)
                status = get_status()

        if status == 'processed_with_error':
            raise AugerException(
                '%s processed with error' % object_readable_name)
        elif status == 'error' or status == "failure":
            raise AugerException('Auger Cloud return error...')

        if post_check_status:
            post_check_status(status)

        return status
