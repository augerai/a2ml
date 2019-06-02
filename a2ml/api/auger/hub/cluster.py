from a2ml.api.auger.hub.hub_api import HubApi
from a2ml.api.auger.hub.base import AugerBaseApi


class AugerClusterApi(AugerBaseApi):
    """Wrapper around HubApi for Auger Cluster."""

    def __init__(self, project_api, cluster_id=None):
        super(AugerClusterApi, self).__init__(
            project_api, None, cluster_id)
        assert project_api is not None, 'Project must be set for Cluster'

    def is_running(self):
        if self.object_id is None:
            return False
        return self.properties().get('status') == 'running'

    def create(self):
        params = {
            'project_id': self.parent_api.object_id,
            'organization_id': self.parent_api.parent_api.object_id}
        params.update(self.get_cluster_settings())
        return self._call_create(params,
            ['waiting', 'provisioning', 'bootstrapping'])

    @staticmethod
    def get_cluster_settings():
        config = HubApi().get_config('auger')

        default_stack = "stable"
        if 'staging' in HubApi().api_url:
            default_stack = 'experimental'

        settings = {
            "kubernetes_stack":
                config.get('cluster/kubernetes_stack', default_stack),
            "autoterminate_minutes":
                config.get('cluster/autoterminate_minutes', 30)
        }

        docker_image_tag = config.get('cluster/docker_image_tag', None)
        if docker_image_tag is not None:
            settings["docker_image_tag"] = docker_image_tag

        worker_type_id = config.get('cluster/worker_type_id', None)
        if worker_type_id is not None:
            settings.update({
                "worker_type_id": worker_type_id,
                "workers_count": config.get('cluster/workers_count', 2),
            })
        else:
            worker_nodes_count = config.get('cluster/worker_count', 2)
            worker_nodes_count = config.get(
                'cluster/worker_nodes_count', worker_nodes_count)

            settings.update({
                "worker_nodes_count": worker_nodes_count,
                "instance_type": config.get('cluster/instance_type', 'c5.large')
            })
            workers_per_node_count = config.get(
                'cluster/workers_per_node_count', None)
            if workers_per_node_count is not None:
                settings["workers_per_node_count"] = workers_per_node_count

        return settings
