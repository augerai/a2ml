import re
import time

from ..exceptions import AugerException

STATE_POLL_INTERVAL = 10

class AugerBaseApi(object):
    """Auger API base class implements common business object calls."""

    def __init__(
        self, ctx, parent_api,
        object_name=None, object_id=None):
        super(AugerBaseApi, self).__init__()
        self.parent_api = parent_api
        self.object_id = object_id
        self.object_name = object_name
        self.rest_api = ctx.rest_api
        self._set_api_request_path()
        self.ctx = ctx

    def list(self, params=None):
        params = {} if params is None else params
        if self.parent_api:
            api_request_path = self.parent_api.api_request_path
            params['%s_id' % api_request_path] = self.parent_api.oid
        if self.object_name:
            params['name'] = self.object_name
        return self.rest_api.request_list(
            '%ss' % self.api_request_path, params)

    def properties(self):
        if self.object_id is not None:
            return self.rest_api.call(
                'get_%s' % self.api_request_path, {'id': self.object_id})

        if self.object_name is None:
            raise AugerException(
                'No name or id was specified for %s' % \
                self._get_readable_name())

        alt_name = self.object_name.replace('_', '-')
        for item in iter(self.list()):
            if item['name'] in [self.object_name, alt_name]:
                self.object_id = item.get('id')
                return item

        return None

    def status(self):
        supported_status = ["Cluster", "ClusterTask", "Component",
            "ExperimentSession", "Organization", "Pipeline", "Project",
            "ProjectFile", "SimilarTrialsRequest", "Subscription"]
        if self.object_in_camel_case not in supported_status:
            return self.properties().get(self._get_status_name())
        else:
            return self.rest_api.get_status(
                self.object_in_camel_case, self.oid).\
                get('data').get(self._get_status_name())

    def wait_for_status(self, progress):
        object_readable_name=self._get_readable_name()
        status_value = self.status()
        last_status = ''

        while status_value in progress:
            if status_value != last_status:
                last_status = status_value
                self._log_status(status_value)

            while status_value == last_status:
                time.sleep(STATE_POLL_INTERVAL)
                status_value = self.status()

        if status_value == 'processed_with_error':
            raise AugerException(
                '%s processed with error' % object_readable_name)
        elif status_value == 'error' or status_value == "failure":
            props = self.properties()
            raise AugerException('Auger Cloud return error: %s. Error details: %s'%(props.get('result', ''), props.get('error_message', '')))

        self._log_status(status_value)
        return status_value

    def delete(self):
        self.rest_api.call(
            'delete_%s' % self.api_request_path, {'id': self.oid})

    @property
    def name(self):
        if self.object_name is None:
            properties = self.properties()
            if properties is None:
                raise AugerException(
                    'Can\'t find name for remote %s: %s...' % \
                    (self._get_readable_name(), self.object_id))
            self.object_name = properties.get('name')
        return self.object_name

    @property
    def oid(self):
        return self._ensure_object_id()

    @property
    def is_exists(self):
        return self.properties() != None

    def _get_readable_name(self):
        s = self.api_request_path
        return ' '.join([w.capitalize() for w in s.split('_')])

    def _get_status_name(self):
        return 'status'

    def _log_status(self, status):
        self.ctx.log(
            '%s %s is %s...' % \
            (self._get_readable_name(), self._get_status_name(), status))

    def _call_create(self, params=None, progress=None,has_return_object=True):
        if self.ctx.provider_info:
            provider = list(self.ctx.provider_info.keys())[0]
            params['providers'] = [provider]
            if self.ctx.provider_info[provider].get(self.api_request_path):
                params['provider_info'] = self.ctx.provider_info[provider][self.api_request_path]

        #print("_call_create %s: %s"%(self.api_request_path,params))
        object_properties = self.rest_api.call(
            'create_%s' % self.api_request_path, params)
        if has_return_object:
            if object_properties:
                self.object_id = object_properties.get('id')
                if progress:
                    self.wait_for_status(progress)
            return self.properties()

    def _call_update(self, params=None, progress=None, has_return_object=True):
        if self.ctx.provider_info:
            provider = list(self.ctx.provider_info.keys())[0]
            params['providers'] = [provider]
            if self.ctx.provider_info[provider].get(self.api_request_path):
                params['provider_info'] = self.ctx.provider_info[provider][self.api_request_path]

        #print("_call_update %s: %s"%(self.api_request_path,params))
        object_properties = self.rest_api.call(
            'update_%s' % self.api_request_path, params)

        if has_return_object:
            if object_properties:
                self.object_id = object_properties.get('id')
                if progress:
                    self.wait_for_status(progress)
            return self.properties()

    def _ensure_object_id(self):
        if self.object_id is None:
            properties = self.properties()
            if properties is not None:
                self.object_id = properties.get('id')
            else:
                raise AugerException('Can\'t find remote %s: %s...' % \
                    (self._get_readable_name(), self.object_name))
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
        def to_camel_case(name):
            return ''.join(x.capitalize() for x in name.split('_'))
        def get_api_request_path(name):
            return '_'.join(to_snake_case(name).split('_')[1:-1])

        self.api_request_path = get_api_request_path(
            patch_name if patch_name else type(self).__name__)
        self.object_in_camel_case = to_camel_case(
            self.api_request_path)
