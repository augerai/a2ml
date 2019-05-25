import time

from a2ml.api.auger.hub.hub_api import HubApi
from a2ml.api.auger.credentials import Credentials
from a2ml.api.auger.hub.project import AugerProjectApi
from a2ml.api.auger.hub.cluster import AugerClusterApi
from a2ml.api.auger.hub.org import AugerOrganizationApi


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
        if not self.project_api.is_running():
            self.ctx.log('Starting Project to process request...')
            self.project_api.deploy()

    def _ensure_org_and_project(self):
        """Ensure there are org, project and cluster to work with"""

        org_name = self.ctx.config['auger'].get('org_name', None)
        if org_name is None:
            raise Exception(
                'Please specify your organization (org_name:) in auger.yaml...')

        self.org_api = AugerOrganizationApi(self.hub_client, org_name)
        org_properties = self.org_api.properties()
        if org_properties is None:
            raise Exception('Can\'t find organization %s' % org_name)
        self.org_api.cluster_mode = org_properties.get('cluster_mode')

        project_name = self.ctx.config['auger'].get('project_name', None)
        if project_name is None:
            raise Exception(
                'Please specify your project (project_name:) in auger.yaml...')

        self.project_api = AugerProjectApi(
            self.hub_client, self.org_api, project_name)
        project_properties = self.project_api.properties()
        if project_properties is None:
            self.ctx.log(
                'Can\'t find project %s on the Auger Hub.'
                ' Creating...' % project_name)
            self.project_api.create()
