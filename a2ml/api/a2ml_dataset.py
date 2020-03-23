from a2ml.api.utils.crud_runner import CRUDRunner
from a2ml.api.utils.error_handler import ErrorHandler
class A2MLDataset(metaclass=ErrorHandler):
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

    def list(self):
        return self.runner.execute('list')

    def create(self, source):
        return self.runner.execute('create', source)

    def delete(self, name):
        return self.runner.execute('delete', name)

    def select(self, name):
        return self.runner.execute('select', name)

