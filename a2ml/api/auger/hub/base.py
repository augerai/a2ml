import re
from a2ml.api.auger.hub.hub_api import HubApi


class AugerBaseApi(object):
    """Wrapper around HubApi for basic common calls."""

    def __init__(
        self, parent_api,
        object_name=None, object_id=None):
        super(AugerBaseApi, self).__init__()
        self.parent_api = parent_api
        self.object_id = object_id
        self.object_name = object_name
        self.hub_client = HubApi()
        self._set_api_request_path()

    def list(self, params=None):
        params = {} if params is None else params
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
                'No name or id was specified'
                ' to get %s properties...' % self._get_readable_name())

        alt_name = self.object_name.replace('_', '-')
        for item in iter(self.list()):
            if item['name'] in [self.object_name, alt_name]:
                self.object_id = item.get('id')
                return item

        return None

    def wait_for_status(self, progress):
        return self.hub_client.wait_for_object_status(
            method='get_%s' % self.api_request_path,
            params={'id': self.object_id},
            progress=progress,
            object_readable_name=self._get_readable_name(),
            status_name=self._get_status_name(),
            post_check_status=self._post_check_status,
            log_status=self._log_status)

    @property
    def name(self):
        return self.object_name

    def _get_readable_name(self):
        s = self.api_request_path
        return ' '.join([w.capitalize() for w in s.split('_')])

    def _get_status_name(self):
        return 'status'

    def _log_status(self, status):
        if self.hub_client.ctx is None:
            return
        self.hub_client.ctx.log(
            '%s %s is %s...' % \
            (self._get_readable_name(), self._get_status_name(), status))

    def _post_check_status(self, status, result):
        self._log_status(status)

    def _call_create(self, params=None, progress=None):
        object_properties = self.hub_client.call_hub_api(
            'create_%s' % self.api_request_path, params)
        if object_properties:
            self.object_id = object_properties.get('id')
            if progress:
                object_properties = self.wait_for_status(progress)
        return object_properties

    def _ensure_object_id(self):
        if self.object_id is None:
            obj_properties = self.properties()
            if obj_properties is not None:
                self.object_id = obj_properties.get('id')
            else:
                raise AugerException('Can\'t find id for %s' % self.object_name)
        return self.object_id

    def _get_uniq_object_name(self, prefix, suffix):
        all_similar_names, count = [], 0
        for item in iter(self.list()):
            if prefix in item.get('name'):
                all_similar_names.append(item.get('name'))
                count += 1

        if count == 0:
            return '%s%s' % (prefix, suffix)

        max_tries = count + 100
        while count < max_tries:
            name = '%s-%s%s' % (prefix, count, suffix)
            if name in all_similar_names:
                count += 1
            else:
                return name

        return '%s-%s%s' % (prefix, shortuuid.uuid(), suffix)

    def _set_api_request_path(self, patch_name=None):
        def to_snake_case(name):
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        def get_api_request_path(name):
            return '_'.join(to_snake_case(name).split('_')[1:-1])

        self.api_request_path = get_api_request_path(
            patch_name if patch_name else type(self).__name__)
