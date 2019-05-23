from a2ml.api.auger.hub.hub_api import REQUEST_LIMIT
from a2ml.api.auger.hub.cluster import AugerClusterApi


class AugerProjectApi(object):
    """Wrapper around HubApi for Auger Project."""
    def __init__(self, hub_client, name, org_id, project_id=None):
        super(AugerProjectApi, self).__init__()
        self.name = name
        self.org_id = org_id
        self.hub_client = hub_client
        self.project_id = project_id

    def is_running(self):
        self._ensure_project_id('Can\'t find project %s...' % self.name)
        return self.properties().get('status') == 'running'

    def properties(self):
        if self.project_id is not None:
            return self.hub_client.call_hub_api(
                'get_project', {'id': self.project_id})

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

    def delete(self):
        project_id = self._ensure_project_id(
            'Can\'t find project %s to delete.' % self.name)
        self.hub_client.call_hub_api('delete_project', {'id': project_id})

    def deploy(self, cluster_mode):
        project_id = self._ensure_project_id(
            'Can\'t find project %s to deploy.' % self.name)

        if cluster_mode == 'multi_tenant':
            cluster_settings = AugerClusterApi(
                self.hub_client).get_cluster_settings()

            self.hub_client.call_hub_api('update_project', {
                'id': project_id,
                'cluster_autoterminate_minutes':
                    cluster_settings.get('autoterminate_minutes')
            })
            self.hub_client.call_hub_api('deploy_project', {
                'id': project_id,
                'worker_type_id': cluster_settings.get('worker_type_id'),
                'workers_count' : cluster_settings.get('workers_count'),
                'kubernetes_stack': cluster_settings.get('kubernetes_stack')
            })

        project = self.properties()
        project = self.hub_client.wait_for_object_status(
            method='get_project',
            params={'id': project_id},
            status=project['status'],
            progress=[
                'undeployed', 'deployed', 'deploying'
            ])
        return project

    def _ensure_project_id(self, error_message):
        if self.project_id is None:
            project = self.properties()
            if project is not None:
                self.project_id = project.get('id')
            else:
                raise Exception(error_message)
        return self.project_id
