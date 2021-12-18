from a2ml.api.base_a2ml import BaseA2ML
from a2ml.api.utils.show_result import show_result
#from a2ml.api.utils import convert_source


class A2MLDataset(BaseA2ML):
    """Contains the dataset CRUD operations that interact with provider."""
    def __init__(self, ctx, provider=None):
        """Initializes a new a2ml dataset.

        Args:
            ctx (object): An instance of the a2ml Context.
            provider (str): The automl provider(s) you wish to run. For example 'auger,azure,google'. The default is None - use provider set in config.
        
        Returns:
            A2MLDataset object

        Examples:
            .. code-block:: python

                ctx = Context()
                dataset = A2MLDataset(ctx, 'auger, azure')
        """
        super(A2MLDataset, self).__init__(ctx, 'dataset')
        self.runner = self.build_runner(ctx, provider)

    @show_result
    def list(self):
        """List all of the DataSets for the Project specified in the .yaml.

        Note:
            You will need to user the `iter <https://www.programiz.com/python-programming/methods/built-in/iter>`_ function to access the dataset elements.
        
        Returns:
            Results for each provider. ::

                {
                    'auger': {
                        'result': True,
                        'data': {
                            'datasets': <object> 
                        }
                    }
                }

        Examples:
            .. code-block:: python

                ctx = Context()
                dataset_list = A2MLDataset(ctx, 'auger, azure').list()
                for provider in ['auger', 'azure']
                    if dataset_list[provider].result is True:
                        for dataset in iter(dataset_list[provider].data.datasets):
                            ctx.log(dataset.get('name'))
                    else:
                        ctx.log('error %s' % dataset_list[provider].data)
        """
        return self.runner.execute('list')

    @show_result
    def create(self, source = None, name=None, description=None):
        """Create a new DataSet for the Project specified in the .yaml.

        Args:
            source (str, optional): Local file name, remote url to the data source file, Pandas DataFrame or postgres url
            name (str, optional): Name of dataset, if none then file name used. If source is DataFrame then name should be specified.

        Returns:
            Results for each provider. ::

                    {
                        'auger': {
                            'result': True,
                            'data': {
                                'created': 'dataset.csv' 
                            }
                        }
                    }

        Examples:
            .. code-block:: python

                ctx = Context()
                dataset = DataSet(ctx, 'auger, azure').create('../dataset.csv')
        """
        return self.runner.execute('create', source, name, description)

    @show_result
    def upload(self, source, name=None):
        """Upload file to Auger and get Auger url.

        Args:
            source (str): Local file name, remote url to the data source file, Pandas DataFrame or postgres url
            name (str, optional): Name of dataset, if none then file name used. If source is DataFrame then name should be specified.

        Returns:
            {
                'result': True,
                'data': 'url for the file on Auger Hub'
            }

        Examples:
            .. code-block:: python

            ctx = Context()
            url = DataSet(ctx).upload('../dataset.csv')
        """
        return self.get_runner(False).execute_one_provider('upload', source, name)

    @show_result
    def delete(self, name = None):
        """
        Deletes a DataSet for the Project specified in the .yaml.

        Args:
            name(str): name of dataset.

        Returns:
            Results for each provider. ::

                    {
                        'auger': {
                            'result': True,
                            'data': {
                                'deleted': 'dataset.csv' 
                            }
                        }
                    }

        Examples:
            .. code-block:: python

                ctx = Context()
                DataSet(ctx, 'auger, azure').delete(dataset_name)
                ctx.log('Deleted dataset %s' % dataset_name)
        """
        return self.runner.execute('delete', name)

    @show_result

    def select(self, name = None):
        """
        Sets a DataSet name in the context.

        Args:
            name(str): name of dataset.

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

