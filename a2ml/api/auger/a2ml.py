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

    def deploy(self, model_id, locally=False, review=True, name=None, algorithm=None, score=None, data_path=None ):
        return AugerModel(self.ctx).deploy(model_id, locally, review, name, algorithm, score, data_path)

    def predict(self, model_id, filename, threshold=None, locally=False, data=None, columns=None, predicted_at=None, output=None, no_features_in_result=None):
        return AugerModel(self.ctx).predict(
            model_id, filename, threshold, locally, data, columns, predicted_at, output, no_features_in_result)

    def actuals(self, model_id, filename=None, data=None, columns=None, actuals_at=None, actual_date_column=None, locally=False):
        return AugerModel(self.ctx).actuals(
            model_id, filename, data, columns, actuals_at, actual_date_column, locally)

    def delete_actuals(self, model_id, with_predictions=False, begin_date=None, end_date=None, locally=False):
        return AugerModel(self.ctx).delete_actuals(
            model_id, with_predictions, begin_date, end_date, locally)

    def review(self, model_id):
        return AugerModel(self.ctx).review(model_id)
