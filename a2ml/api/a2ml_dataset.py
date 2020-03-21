from a2ml.api.utils.crud_runner import CRUDRunner
from a2ml.api.utils.error_handler import ErrorHandler

class A2MLDataset(metaclass=ErrorHandler):

    def __init__(self, ctx, provider):
        super(A2MLDataset, self).__init__()
        self.ctx = ctx
        self.runner = CRUDRunner(ctx, provider, 'dataset')
        self.showresult = True

    def list(self):
        results = self.runner.execute('list')
        if self.showresult:
            self.ctx.log(results)
        return results

    def create(self, source = None):
        results = self.runner.execute('create', source)
        if self.showresult:
            self.ctx.log(results)
        return results

    def delete(self, name = None):
        results = self.runner.execute('delete', name)
        if self.showresult:
            self.ctx.log(results)
        return results

    def select(self, name = None):
        results = self.runner.execute('select', name)
        if self.showresult:
            self.ctx.log(results)
        return results
