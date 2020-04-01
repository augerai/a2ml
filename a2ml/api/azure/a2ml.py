from a2ml.api.azure.model import AzureModel
from a2ml.api.azure.dataset import AzureDataset
from a2ml.api.azure.experiment import AzureExperiment

class AzureA2ML(object):
    """Auger A2ML implementation."""

    def __init__(self, ctx):
        super(AzureA2ML, self).__init__()
        self.ctx = ctx

    def import_data(self):
        return AzureDataset(self.ctx).create()

    def train(self):
        return AzureExperiment(self.ctx).start()

    def evaluate(self, run_id = None):
        return AzureExperiment(self.ctx).leaderboard(run_id)

    def deploy(self, model_id, locally=False):
        return AzureModel(self.ctx).deploy(model_id, locally)

    def predict(self, filename, model_id, threshold=None, locally=False):
        return AzureModel(self.ctx).predict(
            filename, model_id, threshold, locally)

    def review(self):
        pass
