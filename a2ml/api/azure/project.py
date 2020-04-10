from azureml.core import Workspace
from azureml.exceptions import WorkspaceException
from .exceptions import AzureException
from .decorators import error_handler
from .credentials import Credentials

class AzureProject(object):

    def __init__(self, ctx):
        super(AzureProject, self).__init__()
        self.ctx = ctx
        self.credentials = Credentials(self.ctx).load()
        self.credentials.verify()

    @error_handler    
    def list(self):
        workspaces = Workspace.list(
            self.credentials.subscription_id,
            auth=self.credentials.get_serviceprincipal_auth())
        for project in iter(workspaces.keys()):
            self.ctx.log(project)
        return {'projects': workspaces.keys()}

    @error_handler    
    def create(self, name):
        name = self._get_name(name)
        region = self.ctx.config.get('cluster/region', 'eastus2')
        resource_group = self.ctx.config.get(
            'resource_group', name+'-resources')
        self.ctx.log('Creating %s' % name)

        self.ws = Workspace.create(
            name=name,
            subscription_id=self.credentials.subscription_id,
            resource_group=resource_group,
            create_resource_group=True,
            location=region,
            auth=self.credentials.get_serviceprincipal_auth())
        self._select(name)
        self.ctx.log('%s created' % name)
        return {'created': name}

    @error_handler    
    def delete(self, name):
        name = self._get_name(name)
        ws = Workspace.get(
            name, 
            subscription_id=self.credentials.subscription_id, 
            auth=self.credentials.get_serviceprincipal_auth())
        self.ctx.log('Deleting %s' % name)
        ws.delete(delete_dependent_resources=True, no_wait=False)
        self._select(None)
        self.ctx.log('%s deleted' % name)
        return {'deleted': name}

    @error_handler    
    def select(self, name = None):
        self._select(name)
        self.ctx.log('Selected project %s' % name)
        return {'selected': name}

    def _select(self, name):
        self.ctx.config.set('config', 'name', name)
        self.ctx.config.write('config')

    def _get_name(self, name = None):
        if name is None:
            name =  self.ctx.config.get('name', None)
        if name is None:
            raise AzureException('Please provide project name...')
        return name

    def _get_ws(self, name = None, create_if_not_exist = False):
        name = self._get_name(name)
        try:
            self.ws = Workspace.get(
                name, 
                subscription_id=self.credentials.subscription_id, 
                auth=self.credentials.get_serviceprincipal_auth())
        except Exception as e:
            if create_if_not_exist:
                self.create(name)
            else:
                raise e
        return self.ws
