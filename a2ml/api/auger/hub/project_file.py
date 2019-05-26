from a2ml.api.auger.hub.base import AugerBaseApi


class AugerProjectFileApi(AugerBaseApi):
    """Wrapper around HubApi for Auger ProjectFile Api."""

    def __init__(self,
        hub_client, project_api=None,
        project_file_name=None, project_file_id=None):
        super(AugerProjectFileApi, self).__init__(
            hub_client, project_api,
            project_file_name, project_file_id)
        assert project_api is not None, 'Project must be set for Project File'

    def create(self, file_url, file_name=None):
        return self._call_create({
            'name': self.object_name,
            'project_id': self.parent_api.object_id,
            'file_name': file_name, 'url': file_url}, ['processing'])
