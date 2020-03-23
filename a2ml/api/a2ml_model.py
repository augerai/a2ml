from a2ml.api.utils.crud_runner import CRUDRunner
from a2ml.api.utils.error_handler import ErrorHandler

class A2MLModel(metaclass=ErrorHandler):

    def __init__(self, ctx, provider):
        super(A2MLModel, self).__init__()
        self.ctx = ctx
        self.runner = CRUDRunner(ctx, provider, 'model')

    def deploy(self, model_id, locally):
        return self.runner.execute('deploy', model_id, locally)

    def predict(self, filename, model_id, threshold, locally):
        return self.runner.execute('predict', filename, model_id, threshold, locally)

    def actual(self, filename, model_id):
        return self.runner.execute('actual', filename, model_id)
