from auger.api.cloud.rest_api import RestApi
from auger.api.credentials import Credentials
from auger.api.cloud.project import AugerProjectApi
from auger.api.cloud.org import AugerOrganizationApi


class AugerBase(object):
    """Auger Base allows start Project and Cluster"""

    def __init__(self, ctx):
        super(AugerBase, self).__init__()
        self.ctx = ctx
        self.credentials = Credentials(ctx).load()
        self.ctx.rest_api = RestApi(
            self.credentials.api_url, self.credentials.token, debug=self.ctx.debug)

    def start_project(self):
        self._ensure_org_and_project()
        if not self.project_api.is_running():
            self.ctx.log('Starting Project to process request...')
            self.project_api.start()

    def _ensure_org_and_project(self):
        """Ensure there are org and project to work with"""

        org_name = self.credentials.organization
        if org_name is None:
            raise Exception(
                'Please specify your organization...')

        self.org_api = AugerOrganizationApi(self.ctx, org_name)
        org_properties = self.org_api.properties()
        if org_properties is None:
            raise Exception('Can\'t find organization %s' % org_name)
        self.org_api.cluster_mode = org_properties.get('cluster_mode')

        project_name = self.ctx.config['config'].get('name', None)
        if project_name is None:
            raise Exception(
                'Please specify your project in config.yaml/name...')

        self.project_api = AugerProjectApi(
            self.ctx, self.org_api, project_name)
        project_properties = self.project_api.properties()
        if project_properties is None:
            self.ctx.log(
                'Can\'t find project %s on the Auger Cloud.'
                ' Creating...' % project_name)
            self.project_api.create()

    @classmethod
    def _error_handler(cls, decorated):
        def wrapper(self, *args, **kwargs):
            try:
                return decorated(self, *args, **kwargs)
            except Exception as exc:
                # TODO refactor into reusable exception handler
                # with comprehensible user output
                if self.ctx.debug:
                    import traceback
                    traceback.print_exc()
                self.ctx.log(str(exc))
        return wrapper
