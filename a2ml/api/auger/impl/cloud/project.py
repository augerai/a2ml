import time
from .base import AugerBaseApi
from .cluster import AugerClusterApi
from ..exceptions import AugerException


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
        project_properties = self.properties()
        if project_properties.get('status') != 'running':
            self.ctx.log('Starting Project...')
            self._do_start(project_properties)
            self.ctx.log('Started Project %s' % self.object_name)
        # else:
        #     self.ctx.log('Project is already running...')

        self._update_cluster_settings()

    def _update_cluster_settings(self):
        project_properties = self.properties()

        cluster_id = project_properties.get('cluster_id')
        cluster_api = AugerClusterApi(self.ctx, self, cluster_id)
        cluster_settings = cluster_api.get_cluster_settings(self.ctx)

        update_properties = {}
        props_to_update = ['worker_type_id', 'workers_count', 'kubernetes_stack']
        for prop in props_to_update:
            if project_properties.get(prop, cluster_settings.get(prop)) != cluster_settings.get(prop):
                update_properties[prop] = cluster_settings.get(prop)

        if update_properties:
            self.ctx.log('Update project cluster: %s' % update_properties)

            update_properties['id'] = self.object_id
            self._call_update(update_properties, progress=['undeployed', 'deployed', 'scaling', 'zero_scaled', 'deploying'])
                
    def _do_start(self, project_properties):
        self._ensure_object_id()
        status = project_properties.get('status')

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
            # self.rest_api.call('update_project', {
            #     'id': self.object_id,
            #     'cluster_autoterminate_minutes':
            #         cluster_settings.get('autoterminate_minutes')})
            try:
                self.rest_api.call('deploy_project', {
                    'id': self.object_id,
                    'worker_type_id': cluster_settings.get('worker_type_id'),
                    'workers_count' : cluster_settings.get('workers_count'),
                    'kubernetes_stack': cluster_settings.get('kubernetes_stack')})
            except:
                project_properties = self.properties()
                status = project_properties.get('status')
                project_status = ['deployed', 'deploying', 'running']
                if not status in project_status:
                    raise                    

        result = self.wait_for_status(
            ['undeployed', 'deployed', 'scaling', 'zero_scaled', 'deploying'])
        time.sleep(20)
        return result

    def stop(self):
        if self.status() != 'undeployed':
            self.rest_api.call(
                'undeploy_project', {'id': self.object_id})
            return self.wait_for_status(['running', 'undeploying'])
