from a2ml.api.base_a2ml import BaseA2ML
from a2ml.api.utils.show_result import show_result

class A2MLModel(BaseA2ML):

    def __init__(self, ctx, provider):
        super(A2MLModel, self).__init__()
        self.ctx = ctx
        self.provider = provider

        def build_runner(locally=False):
            return self.build_runner(ctx, provider, 'model', force_local=locally)

        self.runner = build_runner

    @show_result
    def deploy(self, model_id, locally):
        return self.runner(locally).execute('deploy', model_id, locally)

    @show_result
    def predict(self, filename, model_id, threshold, locally):
        return self.runner(locally).execute('predict', filename, model_id, threshold, locally)

    @show_result
    def actual(self, filename, model_id):
        return self.runner().execute('actual', filename, model_id)
