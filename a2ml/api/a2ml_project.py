from a2ml.api.base_a2ml import BaseA2ML
from a2ml.api.utils.show_result import show_result

class A2MLProject(BaseA2ML):
    """Contains the project CRUD operations that interact with provider."""
    def __init__(self, ctx, provider=None):
        """Initializes a new a2ml project.

        Args:
            ctx (object): An instance of the a2ml Context.
            provider (str): The automl provider(s) you wish to run. For example 'auger,azure,google'. The default is None - use provider set in config.
        
        Returns:
            A2MLProject object

        Examples:
            .. code-block:: python

                ctx = Context()
                project = A2MLDataset(ctx, 'auger, azure')
        """
        super(A2MLProject, self).__init__(ctx, 'project')
        self.runner = self.build_runner(ctx, provider)

    @show_result
    def list(self):
        """
        List all of the projects for the specified providers.

        Note:
            You will need to user the `iter <https://www.programiz.com/python-programming/methods/built-in/iter>`_ function to access the dataset elements.
        

        Returns:
            Results for each provider. ::

                {
                    'auger': {
                        'result': True,
                        'data': {
                            'projects': <object> 
                        }
                    }
                }

        Examples:
            .. code-block:: python

                ctx = Context()
                project_list = A2MLProject(ctx, 'auger, azure').list()
                for provider in ['auger', 'azure']
                    if project_list[provider].result is True:
                        for project in iter(project_list[provider].data.projects):
                            ctx.log(project.get('name'))
                    else:
                        ctx.log('error %s' % project_list[provider].data)
        """
        return self.runner.execute('list')

    @show_result
    def create(self, name):
        """Creates a project for the specified providers.

        Args:
            name(str): name of project. If None - use project name from config.

        Returns:
            Results for each provider. ::

                {
                    'auger': {
                        'result': True,
                        'created': 'project_name'
                    }
                }

        Examples:
            .. code-block:: python

                ctx = Context()
                project_list = A2MLProject(ctx, 'auger, azure').create('new_project_name')


        """
        return self.runner.execute('create', name)

    @show_result
    def delete(self, name):
        """Deletes a project for the specified providers.

        Args:
            name(str): name of project. If None - use project name from config.

        Returns:
            Results for each provider. ::

                {
                    'auger': {
                        'result': True,
                        'deleted': 'existing_project_name'
                    }
                }

        Examples:
            .. code-block:: python

                ctx = Context()
                project_list = A2MLProject(ctx, 'auger, azure').delete('existinng_project_name')

        """
        return self.runner.execute('delete', name)

    @show_result
    def select(self, name):
        """Sets a Project name in the context.

        Args:
            name(str): name of project. name(str): name of project. If None - use project name from config.

        Returns:
            Results for each provider. ::

                {
                    'auger': {
                        'result': True,
                        'data': {
                            'selected': 'fortunetest'
                        }
                    }
                }

        Examples:
            .. code-block:: python

                ctx = Context()
                DataSet(ctx, 'auger, azure').select(dataset_name)
        """
        return self.runner.execute('select', name)

    @show_result
    def get_cluster_config(self, name, local_config=True):
        """Get project cluster configuration for the specified providers.

        Args:
            name(str): name of project. If None - use project name from config.
            local_config(bool): If True, return cluster parameters from local config, otherwise from remote cluster

        Returns:
            Results for each provider. ::

                {
                    'auger': {
                        'result': True,
                        'data': {
                            'type': 'standard',
                            'min_nodes': 2,
                            'max_nodes': 2,
                            'stack_version': 'stable'
                        }
                    },
                    'azure': {
                        'result': True,
                        'data': {
                            'region': 'eastus2',
                            'min_nodes': 0,
                            'max_nodes': 2,
                            'type': 'STANDARD_D2_V2',
                            'name': 'a2ml-azure',
                            'idle_seconds_before_scaledown': 120
                        }
                    }                    
                }

        Examples:
            .. code-block:: python

                ctx = Context()
                cluster_config = A2MLProject(ctx, 'auger, azure').get_cluster_config()

        """        
        return self.runner.execute('get_cluster_config', local_config)

    @show_result
    def update_cluster_config(self, name, params):
        """Update project cluster configuration for the specified providers.

        Args:
            name(str): name of project. If None - use project name from config.
            params(dict): cluster parameters to update.

        Returns:
            Results for each provider. ::

                {
                    'auger': {
                        'result': True,
                        'data': None
                    },
                    'azure': {
                        'result': True,
                        'data': None
                    }                    
                }

        Examples:
            .. code-block:: python

                ctx = Context()
                params = {'max_nodes': 4}
                cluster_config = A2MLProject(ctx, 'auger, azure').update_cluster_config(params)

        """                
        return self.runner.execute('update_cluster_config', name, params)
