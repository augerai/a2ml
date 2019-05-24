from a2ml.api.auger.hub.hub_api import HubApi


class AugerProjectFileApi(object):
    """Wrapper around HubApi for Auger ProjectFile Api."""
    def __init__(self, hub_client, project_id):
        super(AugerProjectFileApi, self).__init__()
        self.hub_client = hub_client
        self.project_id = project_id

    def list(self):
        params = {'project_id': self.project_id}
        return self.hub_client.request_list('project_files', params)

    def create(self, data_source_name, filename, file_url):
        project_file = self.hub_client.call_hub_api('create_project_file',
            { 'name': data_source_name, 'project_id': self.project_id,
              'file_name': filename, 'url': file_url })

        if 'id' in project_file:
            project_file = self.hub_client.wait_for_object_status(
                method='get_project_file',
                params={'id': project_file['id']},
                status=project_file['status'],
                progress=[
                    'processing'
                ])
                
        return project_file
