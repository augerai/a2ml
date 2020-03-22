from a2ml.api.utils.crud_runner import CRUDRunner
from a2ml.api.utils.error_handler import ErrorHandler
from a2ml.api.utils.show_result import show_result

class A2MLDataset(metaclass=ErrorHandler):

    def __init__(self, ctx, provider):
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
