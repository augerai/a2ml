from a2ml.api.utils.crud_runner import CRUDRunner
from a2ml.api.utils.show_result import show_result

class A2MLModel(object):

    def __init__(self, ctx, provider):
        super(A2MLModel, self).__init__()
        self.ctx = ctx
        self.runner = CRUDRunner(ctx, provider, 'model')

    @show_result
    def deploy(self, model_id, locally):
        return self.runner.execute('deploy', model_id, locally)

    @show_result
    def predict(self, filename, model_id, threshold, locally):
        return self.runner.execute('predict', filename, model_id, threshold, locally)

    @show_result
    def actual(self, filename, model_id):
        return self.runner.execute('actual', filename, model_id)
