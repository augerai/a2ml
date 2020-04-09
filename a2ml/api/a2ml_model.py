from a2ml.api.base_a2ml import BaseA2ML
from a2ml.api.utils.show_result import show_result

class A2MLModel(BaseA2ML):

    def __init__(self, ctx, provider):
        super(A2MLModel, self).__init__()
        self.ctx = ctx
        self.provider = provider
        self.runner = self.build_runner(ctx, provider, 'model')

    @show_result
    def deploy(self, model_id, locally):
        if locally:
            self._redefine_runner_locally()

        return self.runner.execute('deploy', model_id, locally)

    @show_result
    def predict(self, filename, model_id, threshold, locally):
        if locally:
            self._redefine_runner_locally()

        return self.runner.execute('predict', filename, model_id, threshold, locally)

    @show_result
    def actual(self, filename, model_id):
        return self.runner.execute('actual', filename, model_id)

    def _redefine_runner_locally(self):
        self.runner = self.build_runner(self.ctx, self.provider, 'model', force_local=True)
