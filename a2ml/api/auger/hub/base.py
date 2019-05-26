import re


class AugerException(Exception):
    pass

class AugerBaseApi(object):
    """Wrapper around HubApi for basic common calls."""

    def __init__(
        self, hub_client, parent_api,
        object_name=None, object_id=None):
        super(AugerBaseApi, self).__init__()
        self.parent_api = parent_api
        self.hub_client = hub_client
        self.object_id = object_id
        self.object_name = object_name
        self._set_api_request_path()

    def list(self):
        params = {}
        if self.parent_api:
            api_request_path = self.parent_api.api_request_path
            params['%s_id' % api_request_path] = self.parent_api.object_id
        if self.object_name:
            params['name'] = self.object_name
        return self.hub_client.request_list(
            '%ss' % self.api_request_path, params)

    def properties(self):
        if self.object_id is not None:
            return self.hub_client.call_hub_api(
                'get_%s' % self.api_request_path, {'id': self.object_id})

        if self.object_name is None:
            raise AugerException(
                'No name or id wasn\'t specified'
                ' to get %s properties...' % self.get_readable_name())

        alt_name = self.object_name.replace('_', '-')
        for item in iter(self.list()):
            if item['name'] in [self.object_name, alt_name]:
                self.object_id = item.get('id')
                return item

        return None

    def ensure_object_id(self):
        if self.object_id is None:
            obj_properties = self.properties()
            if obj_properties is not None:
                self.object_id = obj_properties.get('id')
            else:
                raise AugerException('Can\'t find id for %s' % self.object_name)
        return self.object_id

    def wait_for_status(self, progress):
        return self.hub_client.wait_for_object_status(
            method='get_%s' % self.api_request_path,
            params={'id': self.object_id},
            progress=progress,
            object_readable_name=self.get_readable_name())

    def get_readable_name(self):
        s = self.api_request_path
        return ' '.join([w.capitalize() for w in s.split('_')])

    def _call_create(self, params=None, progress=None):
        object_properties = self.hub_client.call_hub_api(
            'create_%s' % self.api_request_path, params)
        if object_properties:
            self.object_id = object_properties.get('id')
            if progress:
                object_properties = self.wait_for_status(progress)
        return object_properties

    def _set_api_request_path(self, patch_name=None):
        def to_snake_case(name):
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        def get_api_request_path(name):
            return '_'.join(to_snake_case(name).split('_')[1:-1])

        self.api_request_path = get_api_request_path(
            patch_name if patch_name else type(self).__name__)
