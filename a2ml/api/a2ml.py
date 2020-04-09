from a2ml.api.base_a2ml import BaseA2ML
from a2ml.api.utils.show_result import show_result


class A2ML(BaseA2ML):
    """Facade to A2ML providers."""

    def __init__(self, ctx, provider = None):
        super(A2ML, self).__init__()
        self.ctx = ctx
        self.runner = self.build_runner(ctx, provider)
        self.local_runner = lambda: self.build_runner(ctx, provider, force_local=True)

    @show_result
    def import_data(self):
        return self.runner.execute('import_data')

    @show_result
    def train(self):
        return self.runner.execute('train')

    @show_result
    def evaluate(self, run_id = None):
        return self.runner.execute('evaluate', run_id = run_id)

    @show_result
    def deploy(self, model_id, locally=False):
        return self.__get_runner(locally).execute('deploy', model_id, locally)

    @show_result
    def predict(self, filename, model_id, threshold=None, locally=False):
        return self.__get_runner(locally).execute('predict', filename, model_id, threshold, locally)

    @show_result
    def review(self):
        return self.runner.execute('review')

    def __get_runner(self, locally):
        if locally:
            return self.local_runner()
        else:
            return self.runner
