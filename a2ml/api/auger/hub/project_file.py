from a2ml.api.auger.hub.hub_api import HubApi


class AugerProjectFileApi(object):
    """Wrapper around HubApi for Auger ProjectFile Api."""
    def __init__(self, hub_client):
        super(AugerProjectFileApi, self).__init__()
        self.hub_client = hub_client

    def create(self, project_id, data_source_name, filename, file_url):
        return self.hub_client.call_hub_api('create_project_file',
            { 'name': data_source_name, 'project_id': project_id,
              'file_name': filename, 'url': file_url })
