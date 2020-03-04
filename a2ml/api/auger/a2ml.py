from a2ml.api.auger.deploy import AugerDeploy
from a2ml.api.auger.predict import AugerPredict

from a2ml.api.auger.dataset import AugerDataset
from a2ml.api.auger.experiment import AugerExperiment

class AugerA2ML(object):
    """Auger A2ML implementation."""

    def __init__(self, ctx):
        super(AugerA2ML, self).__init__()
        self.ctx = ctx

    def import_data(self):
        return AugerDataset(self.ctx).create()

    def train(self):
        return AugerExperiment(self.ctx).start()

    def evaluate(self):
        return AugerExperiment(self.ctx).leaderboard()

    def deploy(self, model_id, locally=False):
        AugerDeploy(self.ctx).deploy(model_id, locally)

    def predict(self, filename, model_id, threshold=None, locally=False):
        AugerPredict(self.ctx).predict(filename, model_id, threshold, locally)

    def review(self):
        pass
