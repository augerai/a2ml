from .base import AugerBaseApi
from ..exceptions import AugerException


class AugerClusterTaskApi(AugerBaseApi):
    """Auger Cluster Task Api."""

    def __init__(self, ctx, project_api=None,
        cluster_task_name=None, cluster_task_id=None):
        super(AugerClusterTaskApi, self).__init__(
            ctx, project_api, cluster_task_name, cluster_task_id)

    def create(self, task_args):
        return self._call_create({
            'name': self.object_name,
            'project_id': self.parent_api.object_id,
            'args_encoded': task_args},
            ['pending', 'received', 'started', 'retry']).get('result')
