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

    def create(self, data_source_name, filename, file_url):
        project_file_properties = self.hub_client.call_hub_api(
            'create_project_file', {'name': data_source_name,
            'project_id': self.parent_api.object_id,
            'file_name': filename, 'url': file_url})

        if project_file_properties:
            self.object_id = project_file_properties.get('id')
            project_file_properties = self.wait_for_status(['processing'])

        return project_file_properties
