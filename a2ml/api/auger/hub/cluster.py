from a2ml.api.auger.hub.hub_api import HubApi


class AugerClusterApi(object):
    """Wrapper around HubApi for Auger Cluster."""
    def __init__(self, hub_client, cid=None):
        super(AugerClusterApi, self).__init__()
        self.cid = cid
        self.hub_client = hub_client

    def properties(self):
        return self.hub_client.call_hub_api('get_cluster', {'id': self.cid})

    def is_running(self):
        if self.cid is None:
            return False
        return self.properties().get('status') == 'running'

    def create(self, org_id, project_id, cluster_settings=None):
        params = {
            'organization_id': org_id,
            'project_id': project_id
        }
        if cluster_settings is None:
            cluster_settings = self.get_cluster_settings()
        params.update(cluster_settings)

        cluster = self.hub_client.call_hub_api('create_cluster', params)

        if 'id' in cluster:
            self.cid = cluster['id']
            cluster = self.hub_client.wait_for_object_status(
                method='get_cluster',
                params={'id': cluster['id']},
                status=cluster['status'],
                progress=[
                    'waiting', 'provisioning', 'bootstrapping'
                ])

        return cluster

    def get_cluster_settings(self):
        config = self.hub_client.config

        default_stack = "stable"
        if 'staging' in self.hub_client.api_url:
            default_stack = 'experimental'

        settings = {
            "kubernetes_stack": config.get('cluster/kubernetes_stack', default_stack),
            "autoterminate_minutes": config.get('cluster/autoterminate_minutes', 30)
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
                "instance_type": config.get('cluster/instance_type', 'c5.large'),
            })
            workers_per_node_count = config.get(
                'cluster/workers_per_node_count', None)
            if workers_per_node_count is not None:
                settings["workers_per_node_count"] = workers_per_node_count

        return settings
