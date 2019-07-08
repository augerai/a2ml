from a2ml.api.utils.error_handler import ErrorHandler
from a2ml.api.utils.provider_runner import ProviderRunner


class A2ML(metaclass=ErrorHandler):
    """Facade to A2ML providers."""

    def __init__(self, ctx):
        super(A2ML, self).__init__()
        self.ctx = ctx
        self.runner = ProviderRunner(ctx)

    def import_data(self):
        self.runner.execute('import_data')

    def train(self):
        self.runner.execute('train')

    def evaluate(self):
        self.runner.execute('evaluate')

    def deploy(self, model_id, locally=False):
        self.runner.execute('deploy', model_id, locally)

    def predict(self, filename, model_id, threshold=None, locally=False):
        self.runner.execute('predict', filename, model_id, threshold, locally)

    def review(self):
        self.runner.execute('review')
