import re
import time

from azureml.core import Workspace
from azureml.core.compute import AmlCompute
from azureml.core.compute import ComputeTarget

from .exceptions import AzureException
from a2ml.api.utils.decorators import error_handler, authenticated
from .credentials import Credentials


class AzureProject(object):

    def __init__(self, ctx):
        super(AzureProject, self).__init__()
        self.ctx = ctx
        self.credentials = Credentials(self.ctx).load()

    @error_handler
    @authenticated
    def list(self):
        workspaces = Workspace.list(
            self.credentials.subscription_id,
            auth=self.credentials.get_serviceprincipal_auth())
        for project in iter(workspaces.keys()):
            self.ctx.log(project)
        return {'projects': workspaces.keys()}

    @error_handler
    @authenticated    
    def create(self, name):
        name = self._get_name(name)
        region = self.ctx.config.get('cluster/region', 'eastus2')
        resource_group = self._get_resource_group(name)
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
    @authenticated    
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
    @authenticated    
    def select(self, name = None):
        self._select(name)
        self.ctx.log('Selected project %s' % name)
        return {'selected': name}

    @error_handler
    @authenticated    
    def get_cluster_config(self, name, local_config = True, ws = None):
        result = {
            'name': self._fix_cluster_name(self.ctx.config.get('cluster/name', 'cpucluster'))
        }
        if local_config:
            result.update({
                'min_nodes': int(self.ctx.config.get('cluster/min_nodes',1)),
                'max_nodes': int(self.ctx.config.get('cluster/max_nodes',4)),
                'vm_size': self.ctx.config.get('cluster/type','STANDARD_D2_V2')
            })
            if self.ctx.config.get('cluster/idle_seconds_before_scaledown'):
                result['idle_seconds_before_scaledown'] = self.ctx.config.get('cluster/idle_seconds_before_scaledown')
        else:
            if ws is None:
                ws = self._get_ws(name=name)

            if result['name'] in ws.compute_targets:
                compute_target = ws.compute_targets[result['name']]
                if compute_target and type(compute_target) is AmlCompute:
                    #scale_settings: {'minimum_node_count': 0, 'maximum_node_count': 4, 'idle_seconds_before_scaledown': 120}
                    ct_status = compute_target.get_status()
                    if ct_status:
                        result.update({
                            'min_nodes': ct_status.scale_settings.minimum_node_count,
                            'max_nodes': ct_status.scale_settings.maximum_node_count,
                            'vm_size': ct_status.vm_size,
                            'idle_seconds_before_scaledown': ct_status.scale_settings.idle_seconds_before_scaledown
                        })

        return result
                
    @error_handler
    @authenticated    
    def update_cluster_config(self, name, params, ws=None, allow_create=True):
        cluster_name = self._fix_cluster_name(self.ctx.config.get('cluster/name', 'cpucluster'))
        if ws is None:
            ws = self._get_ws(name=name)

        if 'type' in params:
            params['vm_size'] = params['type']

        if cluster_name in ws.compute_targets:
            compute_target = ws.compute_targets[cluster_name]
            remote_cluster = self.get_cluster_config(name=name, local_config=False, ws=ws)
            update_properties = {}
            props_to_update = ['min_nodes', 'max_nodes', 'vm_size', 'idle_seconds_before_scaledown']
            for prop in props_to_update:
                if params.get(prop) is not None and remote_cluster.get(prop, params.get(prop)) != params.get(prop):
                    update_properties[prop] = params.get(prop)

            if update_properties.get('vm_size'):
                self.ctx.log('Delete existing AML compute context, since cluster type has been changed to %s.'%(update_properties.get('vm_size')))
                compute_target.delete()        
            elif update_properties:
                self.ctx.log('Update compute target %s: %s' % (cluster_name, update_properties))
                compute_target.update(**update_properties)

            try:
                compute_target.wait_for_completion(show_output = True)
            except Exception as e:
                self.ctx.log_debug(str(e))                            

            if not update_properties.get('vm_size'):
                return cluster_name

        if not allow_create:
            raise AzureException("Compute target %s does not exist."%cluster_name)

        self.ctx.log('Creating new AML compute context %s...'%cluster_name)
        provisioning_config = AmlCompute.provisioning_configuration(
            vm_size=params.get('vm_size'), min_nodes=params.get('min_nodes'),
            max_nodes=params.get('max_nodes'), idle_seconds_before_scaledown=params.get('idle_seconds_before_scaledown'))
        compute_target = ComputeTarget.create(
            ws, cluster_name, provisioning_config)
        compute_target.wait_for_completion(show_output = True)

        return cluster_name

    @staticmethod    
    def _fix_cluster_name(name):
        # Name can include letters, digits and dashes.
        # It must start with a letter, end with a letter or digit,
        # and be between 2 and 16 characters in length.
        #TODO check for all conditions

        name = re.sub(r'\W+', '-', name)
        name = name.replace('_','-')[:16]
        if name[0].isdigit():
            test = list(name)
            test[0] = 'C'
            name = ''.join(test)
        if name[-1].isdigit():
            test = list(name)
            test[-1] = 'C'
            name = ''.join(test)

        return name

    def _select(self, name):
        self.ctx.config.set('name', name)
        self.ctx.config.write()

    def _get_name(self, name = None):
        if name is None:
            name =  self.ctx.config.get('name', None)
        if name is None:
            raise AzureException('Please provide project name...')
        return name

    def _get_ws(self, name = None, create_if_not_exist = False):
        name = self._get_name(name)
        nTry = 0
        while True:
            try:
                self.ws = Workspace.get(
                    name, 
                    subscription_id=self.credentials.subscription_id, 
                    auth=self.credentials.get_serviceprincipal_auth(),
                    resource_group=self._get_resource_group(name)
                )
                break
            except Exception as e:
                message = str(e)
                if ('Workspaces not found' in message or 'No workspaces found' in message) and create_if_not_exist:
                    self.create(name)
                    break
                elif 'invalid_client' in message and nTry < 20:
                    self.ctx.log('Workspace.get failed with authentication error. Retry.')
                    nTry += 1
                    time.sleep(20) 
                else:    
                    raise

        return self.ws

    def _get_resource_group(self, name):
        resource_group = self.ctx.config.get('resource_group')
        if not resource_group:
            if name == "a2mlworkspacedev":
                resource_group = "a2mldev"
            elif name == "a2mlworkspacestaging":
                resource_group = "a2mlstaging"
            elif name == "a2mlworkspaceprod":
                resource_group = "a2mlprod"
            else:
                resource_group = name+'-resources'

        return resource_group
