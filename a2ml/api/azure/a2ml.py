
class AzureA2ML(object):
    """Auger A2ML implementation."""

    def __init__(self, ctx):
        super(AzureA2ML, self).__init__()
        self.ctx = ctx

    def import_data(self, source=None):
        from a2ml.api.azure.dataset import AzureDataset

        return AzureDataset(self.ctx).create(source=source)

    def train(self):
        from a2ml.api.azure.experiment import AzureExperiment

        return AzureExperiment(self.ctx).start()

    def evaluate(self, run_id = None):
        from a2ml.api.azure.experiment import AzureExperiment

        return AzureExperiment(self.ctx).leaderboard(run_id)

    def deploy(self, model_id, locally=False, review=True):
        from a2ml.api.azure.model import AzureModel

        return AzureModel(self.ctx).deploy(model_id, locally, review)

    def predict(self, filename, model_id, threshold=None, locally=False, data=None, columns=None, predicted_at=None, output=None):
        from a2ml.api.azure.model import AzureModel

        return AzureModel(self.ctx).predict(
            filename, model_id, threshold=threshold, locally=locally, data=data, columns=columns, 
            predicted_at=predicted_at, output=output)

    def actuals(self, model_id, filename=None, actual_records=None, actuals_at=None, locally=False):
        from a2ml.api.azure.model import AzureModel

        return AzureModel(self.ctx).actuals(
            model_id, filename, actual_records, actuals_at, locally)

    def delete_actuals(self, model_id, with_predictions=False, begin_date=None, end_date=None, locally=False):
        from a2ml.api.azure.model import AzureModel

        return AzureModel(self.ctx).delete_actuals(
            model_id, with_predictions, begin_date, end_date, locally)

    def review(self, model_id):
        from a2ml.api.azure.model import AzureModel

        return AzureModel(self.ctx).review(model_id)

