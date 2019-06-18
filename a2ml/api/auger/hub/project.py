from a2ml.api.auger.hub.base import AugerBaseApi
from a2ml.api.auger.hub.cluster import AugerClusterApi


class AugerProjectApi(AugerBaseApi):
    """Wrapper around HubApi for Auger Project."""

    def __init__(self, org_api,
        project_name=None, project_id=None):
        super(AugerProjectApi, self).__init__(
            org_api, project_name, project_id)
        assert org_api is not None, 'Organization must be set for Project'

    def is_running(self):
        return self.properties().get('status') == 'running'

    def create(self):
        return self._call_create({
            'name': self.object_name, 'organization_id': self.parent_api.object_id})

    def delete(self):
        self._ensure_object_id()
        self.hub_client.call_hub_api('delete_project', {'id': self.object_id})

    def start(self):
        self._ensure_object_id()
        project_properties = self.properties()

        status = project_properties.get('status')
        if status == 'running':
            return project_properties
        if status in ['deployed', 'deploying']:
            return self.wait_for_status(['deployed', 'deploying'])

        cluster_id = project_properties.get('cluster_id')
        cluster_api = AugerClusterApi(self, cluster_id)

        if self.parent_api.get_cluster_mode() == 'single_tenant':
            if not cluster_api.is_running():
                cluster_api.create()
        else:
            cluster_settings = cluster_api.get_cluster_settings()
            self.hub_client.call_hub_api('update_project', {
                'id': self.object_id,
                'cluster_autoterminate_minutes':
                    cluster_settings.get('autoterminate_minutes')})
            self.hub_client.call_hub_api('deploy_project', {
                'id': self.object_id,
                'worker_type_id': cluster_settings.get('worker_type_id'),
                'workers_count' : cluster_settings.get('workers_count'),
                'kubernetes_stack': cluster_settings.get('kubernetes_stack')})

        return self.wait_for_status(['undeployed', 'deployed', 'deploying'])

    def stop(self):
        if self.status() != 'undeployed':
            self.hub_client.call_hub_api(
                'undeploy_project', {'id': self.object_id})
            return self.wait_for_status(['running', 'undeploying'])
