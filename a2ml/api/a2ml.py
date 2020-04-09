from a2ml.api.base_a2ml import BaseA2ML
from a2ml.api.utils.show_result import show_result


class A2ML(BaseA2ML):
    """Facade to A2ML providers."""

    def __init__(self, ctx, provider = None):
        super(A2ML, self).__init__()
        self.ctx = ctx

        def build_runner(locally=False):
            return self.build_runner(ctx, provider, force_local=locally)

        self.runner = build_runner

    @show_result
    def import_data(self):
        return self.runner().execute('import_data')

    @show_result
    def train(self):
        return self.runner().execute('train')

    @show_result
    def evaluate(self, run_id = None):
        return self.runner().execute('evaluate', run_id = run_id)

    @show_result
    def deploy(self, model_id, locally=False):
        return self.runner(locally).execute('deploy', model_id, locally)

    @show_result
    def predict(self, filename, model_id, threshold=None, locally=False):
        return self.runner(locally).execute('predict', filename, model_id, threshold, locally)

    @show_result
    def review(self):
        return self.runner().execute('review')
