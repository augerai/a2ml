from a2ml.api.utils.error_handler import ErrorHandler
from a2ml.api.utils.provider_runner import ProviderRunner


class A2ML(metaclass=ErrorHandler):
    """Facade to A2ML providers."""

    def __init__(self, ctx, provider = None):
        super(A2ML, self).__init__()
        self.ctx = ctx
        self.runner = ProviderRunner(ctx, provider)
        self.showresult = False

    def import_data(self):
        results = self.runner.execute('import_data')
        if self.showresult:
            self.ctx.log(results)
        return results

    def train(self):
        results = self.runner.execute('train')
        if self.showresult:
            self.ctx.log(results)
        return results

    def evaluate(self, run_id = None):
        results = self.runner.execute('evaluate', run_id = run_id)
        if self.showresult:
            self.ctx.log(results)
        return results

    def deploy(self, model_id, locally=False):
        results = self.runner.execute('deploy', model_id, locally)
        if self.showresult:
            self.ctx.log(results)
        return results

    def predict(self, filename, model_id, threshold=None, locally=False):
        results = self.runner.execute('predict', filename, model_id, threshold, locally)
        if self.showresult:
            self.ctx.log(results)
        return results

    def review(self):
        results = self.runner.execute('review')
        if self.showresult:
            self.ctx.log(results)
        return results
