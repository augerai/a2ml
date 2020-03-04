from a2ml.api.utils.error_handler import ErrorHandler
from a2ml.api.utils.provider_runner import ProviderRunner


class A2ML(metaclass=ErrorHandler):
    """Facade to A2ML providers."""

    def __init__(self, ctx, provider = None):
        super(A2ML, self).__init__()
        self.ctx = ctx
        self.runner = ProviderRunner(ctx, provider)

    def import_data(self):
        results = self.runner.execute('import_data')
        self.ctx.log(results)

    def train(self):
        results = self.runner.execute('train')
        self.ctx.log(results)

    def evaluate(self):
        results = self.runner.execute('evaluate')
        self.ctx.log(results)

    def deploy(self, model_id, locally=False):
        results = self.runner.execute('deploy', model_id, locally)
        self.ctx.log(results)

    def predict(self, filename, model_id, threshold=None, locally=False):
        results = self.runner.execute('predict', filename, model_id, threshold, locally)
        self.ctx.log(results)

    def review(self):
        results = self.runner.execute('review')
        self.ctx.log(results)
