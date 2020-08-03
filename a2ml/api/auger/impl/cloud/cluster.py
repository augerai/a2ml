from .base import AugerBaseApi
from ..exceptions import AugerException


class AugerClusterApi(AugerBaseApi):
    """Auger Cluster API."""

    def __init__(self, ctx, project_api, cluster_id=None):
        super(AugerClusterApi, self).__init__(
            ctx, project_api, None, cluster_id)
        assert project_api is not None, 'Project must be set for Cluster'

    def is_running(self):
        if self.object_id is None:
            return False
        return self.properties().get('status') == 'running'

    def create(self):
        params = {
            'project_id': self.parent_api.object_id,
            'organization_id': self.parent_api.parent_api.object_id}
        params.update(self.get_cluster_settings(self.ctx))
        return self._call_create(params,
            ['waiting', 'provisioning', 'bootstrapping'])

    @staticmethod
    def get_cluster_settings(ctx):
        config = ctx.config

        default_stack = "stable"
        if 'staging' in ctx.rest_api.api_url:
            default_stack = 'experimental'

        kubernetes_stack = config.get('cluster/kubernetes_stack', None, config_name="auger")
        if kubernetes_stack is None:
            kubernetes_stack = config.get(
                'cluster/stack_version', default_stack, config_name="auger")

        settings = {
            "kubernetes_stack": kubernetes_stack,
            "autoterminate_minutes":
                config.get('cluster/autoterminate_minutes', 30, config_name="auger")
        }

        docker_image_tag = config.get('cluster/docker_image_tag', None, config_name="auger")
        if docker_image_tag is not None:
            settings["docker_image_tag"] = docker_image_tag

        cluster_type = config.get('cluster/type', 'standard', config_name="auger")
        if cluster_type not in ['standard', 'high_memory']:
            raise AugerException(
                'Cluster type \'%s\' is not supported' % cluster_type)
        settings.update({
            "worker_type_id": 1 if cluster_type == 'standard' else 3,
            "workers_count": config.get('cluster/max_nodes', 2, config_name="auger"),
        })
        # else: # single tenant settings
        #     worker_nodes_count = config.get('cluster/worker_count', 2)
        #     worker_nodes_count = config.get(
        #         'cluster/worker_nodes_count', worker_nodes_count)

        #     settings.update({
        #         "worker_nodes_count": worker_nodes_count,
        #         "instance_type": config.get('cluster/instance_type', 'c5.large')
        #     })
        #     workers_per_node_count = config.get(
        #         'cluster/workers_per_node_count', None)
        #     if workers_per_node_count is not None:
        #         settings["workers_per_node_count"] = workers_per_node_count

        return settings
