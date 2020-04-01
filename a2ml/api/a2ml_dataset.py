from a2ml.api.utils.crud_runner import CRUDRunner
from a2ml.api.utils.show_result import show_result

class A2MLDataset(object):
    """Contains the dataset CRUD operations that interact with provider."""
    def __init__(self, ctx, provider):
        """Initializes a new a2ml.

        Args:
            provider (str): The automl provider/s you wish to run. For example 'auger,azure,google'.
        Returns:
            A2ML object
        """
        super(A2MLDataset, self).__init__()
        self.ctx = ctx
        self.runner = CRUDRunner(ctx, provider, 'dataset')

    @show_result
    def list(self):
        return self.runner.execute('list')

    @show_result
    def create(self, source = None):
        return self.runner.execute('create', source)

    @show_result
    def delete(self, name = None):
        return self.runner.execute('delete', name)

    @show_result
    def select(self, name = None):
        return self.runner.execute('select', name)

