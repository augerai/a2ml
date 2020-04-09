from a2ml.api.base_a2ml import BaseA2ML
from a2ml.api.utils.show_result import show_result

class A2MLProject(BaseA2ML):

    def __init__(self, ctx, provider):
        super(A2MLProject, self).__init__()
        self.ctx = ctx
        self.runner = self.build_runner(ctx, provider, 'project')

    @show_result
    def list(self):
        return self.runner.execute('list')

    @show_result
    def create(self, name):
        return self.runner.execute('create', name)

    @show_result
    def delete(self, name):
        return self.runner.execute('delete', name)

    @show_result
    def select(self, name):
        return self.runner.execute('select', name)
