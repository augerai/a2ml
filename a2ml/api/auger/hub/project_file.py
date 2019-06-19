from a2ml.api.auger.hub.base import AugerBaseApi


class AugerProjectFileApi(AugerBaseApi):
    """Wrapper around HubApi for Auger ProjectFile Api."""

    def __init__(self, project_api=None,
        project_file_name=None, project_file_id=None):
        super(AugerProjectFileApi, self).__init__(
            project_api, project_file_name, project_file_id)
        assert project_api is not None, 'Project must be set for Project File'
        self._set_api_request_path('AugerProjectFileApi')

    def create(self, file_url, file_name=None):
        return self._call_create({
            'name': self.object_name,
            'project_id': self.parent_api.object_id,
            'file_name': file_name, 'url': file_url}, ['processing'])

    def delete(self):
        self.hub_client.call_hub_api(
            'delete_%s' % self.api_request_path, {'id': self.oid})
