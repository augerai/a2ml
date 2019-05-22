from a2ml.api.auger.hub.hub_api import REQUEST_LIMIT


class AugerProjectApi(object):
    """Wrapper around HubApi for Auger Project."""
    def __init__(self, hub_client, name, org_id):
        super(AugerProjectApi, self).__init__()
        self.name = name
        self.org_id = org_id
        self.hub_client = hub_client

    def properties(self):
        projects_list = self.hub_client.call_hub_api('get_projects', {
            'name': self.name,
            'organization_id': self.org_id,
            'limit': REQUEST_LIMIT})

        alt_project_name = self.name.replace('_', '-')

        if len(projects_list) > 0:
            for item in projects_list:
                if item['name'] == self.name:
                    return item

                if item['name'] == alt_project_name:
                    return item

        return None

    def create(self):
        return self.hub_client.call_hub_api('create_project', {
            'name': self.name,
            'organization_id': self.org_id})

    def delete(self, project_id=None):
        if project_id is None:
            project = self.properties()
            if project is None:
                raise Exception('Can\'t find project %s to delete.' % self.name)
            project_id = project.get('id')

        self.hub_client.call_hub_api('delete_project', {'id': project_id})
