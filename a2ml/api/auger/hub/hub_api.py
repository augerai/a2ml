import re
import sys
import time

from auger.hub_api_client import HubApiClient
from a2ml.api.auger.hub.base import AugerException

REQUEST_LIMIT = 100
STATE_POLL_INTERVAL = 10

class HubApi(object):
    """Auger Hub Api call wrapper."""
    def __init__(self, ctx, url, token):
        super(HubApi, self).__init__()
        self.hub_client = HubApiClient(hub_app_url=url, token=token)
        self.api_url = url
        self.ctx = ctx

    def get_config(self, name):
        return self.ctx.config[name]

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

    def wait_for_object_status(
        self, method, params, progress,
        object_readable_name, status_name='status'):

        def log_status(obj_status):
            if self.ctx is not None:
                self.ctx.log(
                    '%s %s is %s...' % (object_readable_name, status_name, obj_status))

        result = self.call_hub_api(method, params=params)
        status = result.get(status_name, 'failure')
        last_status = ''

        while status in progress:
            if status != last_status:
                last_status = status
                log_status(status)

            while status == last_status:
                time.sleep(STATE_POLL_INTERVAL)
                result = self.call_hub_api(method, params=params)
                status = result.get(status_name, 'failure')

        if status == 'processed_with_error':
            raise AugerException(
                '%s processed with error' % object_readable_name)

        log_status(status)

        if status == "failure":
            raise AugerException(
                'Auger Hub API call {}({}) failed: {}'.format(
                result.get('name', ""), result.get('args', ""),
                result.get("exception", "")))
        if status == 'error':
            if result.get('errorMessage'):
                raise AugerException(
                    'Auger Hub API return error: {}'.format(
                    result.get('errorMessage')))
            raise AugerException('Auger Hub API return error: {}'.format(result))

        return result
