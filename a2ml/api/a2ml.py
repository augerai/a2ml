from a2ml.api.utils.error_handler import ErrorHandler
from a2ml.api.utils.provider_runner import ProviderRunner


class A2ML(metaclass=ErrorHandler):
    """Facade to A2ML providers."""

    def __init__(self, ctx, provider = None):
        super(A2ML, self).__init__()
        self.ctx = ctx
        self.runner = ProviderRunner(ctx, provider)

    def import_data(self):
        return self.runner.execute('import_data')

    def train(self):
        return self.runner.execute('train')

    def evaluate(self):
        return self.runner.execute('evaluate')

    def deploy(self, model_id, locally=False):
        return self.runner.execute('deploy', model_id, locally)

    def predict(self, filename, model_id, threshold=None, locally=False):
        return self.runner.execute('predict', filename, model_id, threshold, locally)

    def review(self):
        return self.runner.execute('review')
