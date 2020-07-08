from a2ml.api.auger.model import AugerModel
from a2ml.api.auger.dataset import AugerDataset
from a2ml.api.auger.experiment import AugerExperiment

class AugerA2ML(object):
    """Auger A2ML implementation."""

    def __init__(self, ctx):
        super(AugerA2ML, self).__init__()
        self.ctx = ctx

    def import_data(self, source=None):
        return AugerDataset(self.ctx).create(source=source)

    def train(self):
        return AugerExperiment(self.ctx).start()

    def evaluate(self, run_id = None):
        return AugerExperiment(self.ctx).leaderboard(run_id)

    def deploy(self, model_id, locally=False, review=True):
        return AugerModel(self.ctx).deploy(model_id, locally, review)

    def predict(self, filename, model_id, threshold=None, locally=False, data=None, columns=None, output=None):
        return AugerModel(self.ctx).predict(
            filename, model_id, threshold, locally, data, columns, output)

    def actual(self, model_id, filename=None, actual_records=None, locally=False):
        return AugerModel(self.ctx).actual(
            model_id, filename, actual_records, locally)
