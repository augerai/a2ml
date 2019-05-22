import re
import sys
import time

from auger.hub_api_client import HubApiClient

REQUEST_LIMIT = 100
STATE_POLL_INTERVAL = 10

class HubApi(object):
    """Auger Hub Api call wrapper."""
    def __init__(self, url, token, logger=None, config=None):
        super(HubApi, self).__init__()
        self.hub_client = HubApiClient(hub_app_url=url,token=token)
        self.api_url = url
        self.logger = logger
        self.config = config

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

    def wait_for_object_status(self, method, params,
        status, progress, status_name='status'):

        def log_status(obj_status):
            if self.logger is not None:
                self.logger(
                    '%s %s is %s...' % (object_type, status_name, obj_status))

        last_status = ''
        object_type = re.sub(r'\w+_', '', method).capitalize()

        while status in progress:
            if status != last_status:
                last_status = status
                log_status(status)

            while status == last_status:
                time.sleep(STATE_POLL_INTERVAL)
                result = self.call_hub_api(method, params=params)
                status = result.get(status_name, 'failure')

        log_status(status)
        if status == "failure":
            raise Exception('Auger Hub API call {}({}) failed: {}'.format(result.get(
                'name', ""), result.get('args', ""), result.get("exception", "")))
        if status == 'error':
            if result.get('errorMessage'):
                raise Exception('Auger Hub API return error: {}'.format(result.get('errorMessage')))
            raise Exception('Auger Hub API return error: {}'.format(result))

        return result
