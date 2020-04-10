from a2ml.api.base_a2ml import BaseA2ML
from a2ml.api.utils.show_result import show_result

class A2MLModel(BaseA2ML):

    def __init__(self, ctx, provider):
        super(A2MLModel, self).__init__()
        self.ctx = ctx
        self.provider = provider
        self.runner = self.build_runner(ctx, provider, 'model')
        self.local_runner = lambda: self.build_runner(ctx, provider, 'model', force_local=True)

    @show_result
    def deploy(self, model_id, locally):
        return self.__get_runner(locally).execute('deploy', model_id, locally)

    @show_result
    def predict(self, filename, model_id, threshold, locally):
        return self.__get_runner(locally).execute('predict', filename, model_id, threshold, locally)

    @show_result
    def actual(self, filename, model_id):
        return self.execute('actual', filename, model_id)

    def __get_runner(self, locally):
        if locally:
            return self.local_runner()
        else:
            return self.runner
