
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

    def predict(self, filename, model_id, threshold=None, locally=False, data=None, columns=None, output=None):
        from a2ml.api.azure.model import AzureModel

        return AzureModel(self.ctx).predict(
            filename, model_id, threshold, locally, data, columns, output)

    def actual(self, model_id, filename=None, actual_records=None, locally=False):
        from a2ml.api.azure.model import AzureModel

        return AzureModel(self.ctx).actual(
            model_id, filename, actual_records, locally)
