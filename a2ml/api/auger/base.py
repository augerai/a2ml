import time

from a2ml.api.auger.hub.hub_api import HubApi
from a2ml.api.auger.hub.org import AugerOrgApi
from a2ml.api.auger.credentials import Credentials
from a2ml.api.auger.hub.project import AugerProjectApi
from a2ml.api.auger.hub.cluster import AugerClusterApi


class AugerBase(object):
    """Auger Base allows start Project and Cluster"""
    def __init__(self, ctx):
        super(AugerBase, self).__init__()
        self.ctx = ctx
        self.credentials = Credentials(ctx.config['auger']).load()
        self.hub_client = HubApi(
            self.credentials.api_url, self.credentials.token,
            self.ctx.log, self.ctx.config['auger'])

    def start_project(self):
        self._ensure_org_and_project()

        if self.cluster_mode == 'single_tenant':
            self._create_cluster()

        self._deploy_project()

    def _ensure_org_and_project(self):
        """Ensure there are org, project and cluster to work with"""

        org_name = self.ctx.config['auger'].get('org_name', None)
        if org_name is None:
            raise Exception(
                'Please specify your organization (org_name:) in auger.yaml...')

        org = AugerOrgApi(self.hub_client, org_name).properties()
        if org is None:
            raise Exception('Can\'t find organization %s' % org_name)
        self.org_id = org.get('id')
        self.cluster_mode = org.get('cluster_mode')

        self.project_name = self.ctx.config['auger'].get('project_name', None)
        if self.project_name is None:
            raise Exception(
                'Please specify your project (project_name:) in auger.yaml...')

        project_api = AugerProjectApi(
            self.hub_client, self.org_id, self.project_name)
        project = project_api.properties()
        if project is None:
            self.ctx.log(
                'Can\'t find project %s on the Auger Hub. Creating...' %
                self.project_name)
            project = project_api.create()
        self.project_id = project.get('id')
        self.cluster_id = project.get('cluster_id')

    def _deploy_project(self):
        """Call to HUB API to deploy Project"""

        project_api = AugerProjectApi(
            self.hub_client, self.org_id,
            self.project_name, self.project_id)

        if not project_api.is_running():
            self.ctx.log('Starting Project to process request...')
            project_api.deploy(self.cluster_mode)

    def _create_cluster(self):
        """Call to HUB API to create Cluster"""

        cluster_api = AugerClusterApi(self.hub_client, self.cluster_id)
        if not cluster_api.is_running():
            self.ctx.log('Starting Cluster to process request...')
            cluster = cluster_api.create(self.org_id, self.project_id)
            self.cluster_id = cluster.get('id')
