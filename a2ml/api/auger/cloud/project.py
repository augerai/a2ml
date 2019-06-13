from .base import AugerBaseApi
from .cluster import AugerClusterApi


class AugerProjectApi(AugerBaseApi):
    """Auger Project API."""

    def __init__(self, ctx, org_api,
        project_name=None, project_id=None):
        super(AugerProjectApi, self).__init__(
            ctx, org_api, project_name, project_id)
        assert org_api is not None, 'Organization must be set for Project'
        self._set_api_request_path('AugerProjectApi')

    def is_running(self):
        return self.properties().get('status') == 'running'

    def create(self):
        return self._call_create({
            'name': self.object_name, 'organization_id': self.parent_api.oid})

    def start(self):
        self._ensure_object_id()
        project_properties = self.properties()

        status = project_properties.get('status')
        if status == 'running':
            return project_properties
        project_status = ['deployed', 'deploying']
        if status in project_status:
            return self.wait_for_status(project_status)

        cluster_id = project_properties.get('cluster_id')
        cluster_api = AugerClusterApi(self.ctx, self, cluster_id)

        if self.parent_api.get_cluster_mode() == 'single_tenant':
            if not cluster_api.is_running():
                cluster_api.create()
        else:
            cluster_settings = cluster_api.get_cluster_settings(self.ctx)
            self.rest_api.call('update_project', {
                'id': self.object_id,
                'cluster_autoterminate_minutes':
                    cluster_settings.get('autoterminate_minutes')})
            self.rest_api.call('deploy_project', {
                'id': self.object_id,
                'worker_type_id': cluster_settings.get('worker_type_id'),
                'workers_count' : cluster_settings.get('workers_count'),
                'kubernetes_stack': cluster_settings.get('kubernetes_stack')})

        return self.wait_for_status(['undeployed', 'deployed', 'deploying'])

    def stop(self):
        if self.status() != 'undeployed':
            self.rest_api.call(
                'undeploy_project', {'id': self.object_id})
            return self.wait_for_status(['running', 'undeploying'])
