from a2ml.api.utils.crud_runner import CRUDRunner
from a2ml.api.utils.error_handler import ErrorHandler

class A2MLProject(metaclass=ErrorHandler):

    def __init__(self, ctx, provider):
        super(A2MLProject, self).__init__()
        self.ctx = ctx
        self.runner = CRUDRunner(ctx, provider, 'project')

    def list(self):
        self.runner.execute('list')

    def create(self, name):
        self.runner.execute('create', name)

    def delete(self, name):
        self.runner.execute('delete', name)

    def select(self, name):
        self.runner.execute('select', name)
