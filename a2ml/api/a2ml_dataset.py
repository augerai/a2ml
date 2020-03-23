from a2ml.api.utils.crud_runner import CRUDRunner
from a2ml.api.utils.error_handler import ErrorHandler

class A2MLDataset(metaclass=ErrorHandler):

    def __init__(self, ctx, provider):
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
