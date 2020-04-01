from azureml.core import Workspace
from azureml.exceptions import WorkspaceException
from azureml.core.authentication import ServicePrincipalAuthentication
from .exceptions import AzureException
from .decorators import error_handler


class AzureProject(object):

    def __init__(self, ctx):
        super(AzureProject, self).__init__()
        self.ctx = ctx

    @error_handler    
    def list(self):
        subscription_id = self.ctx.config.get('subscription_id', None)
        workspaces = Workspace.list(subscription_id)
        for project in iter(workspaces.keys()):
            self.ctx.log(project)
        return {'projects': workspaces.keys()}

    @error_handler    
    def create(self, name):
        name = self._get_name(name)
        subscription_id = self.ctx.config.get('subscription_id', None)
        if subscription_id is None:
            raise AzureException('Please provide Azure subscription id...')
        region = self.ctx.config.get('cluster/region', 'eastus2')
        resource_group = self.ctx.config.get(
            'resource_group', name+'-resources')
        self.ctx.log('Creating %s' % name)

        self.ws = Workspace.create(
            name=name,
            subscription_id=subscription_id,
            resource_group=resource_group,
            create_resource_group=True,
            location=region,
            auth=self._get_ws_auth())
        self._select(name)
        self.ctx.log('%s created' % name)
        return {'created': name}

    @error_handler    
    def delete(self, name):
        name = self._get_name(name)
        subscription_id = self.ctx.config.get('subscription_id', None)
        ws = Workspace.get(name, subscription_id=subscription_id, auth=self._get_ws_auth())
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

    def _get_ws_auth(self):
        import os
        import json
        
        svc_pr = None
        if 'AZURE_CREDENTIALS' in os.environ:
            content = os.environ.get('AZURE_CREDENTIALS', None)
            content = json.loads(content) if content else {}

            if content.get('service_principal_password'):
                svc_pr = ServicePrincipalAuthentication(
                    tenant_id=content.get('service_principal_tenant_id'),
                    service_principal_id=content.get('service_principal_id'),
                    service_principal_password=content.get('service_principal_password'))

        return svc_pr

    def _get_ws(self, name = None, create_if_not_exist = False):
        name = self._get_name(name)
        subscription_id = self.ctx.config.get('subscription_id', None)
        if subscription_id is None:
            raise AzureException('Please provide Azure subscription id...')
        try:
            self.ws = Workspace.get(name, subscription_id=subscription_id, auth=self._get_ws_auth())
        except WorkspaceException as e:
            if create_if_not_exist:
                self.create(name)
            else:
                raise e
        return self.ws
