from a2ml.api.auger.base import AugerBase
from auger.api.cloud.experiment import AugerExperimentApi
from auger.api.cloud.utils.exception import AugerException
from a2ml.api.auger.config import AugerConfig


class AugerTrain(AugerBase):
    """Train you Model on Auger."""

    def __init__(self, ctx):
        super(AugerTrain, self).__init__(ctx)

    @AugerBase._error_handler
    def train(self):
        # verify avalability of auger credentials
        self.credentials.verify()

        self.start_project()

        data_set_name = self.ctx.config['auger'].get('dataset')
        if data_set_name is None:
            raise AugerException(
                'Plese specify DataSet name in auger.yaml/dataset')

        experiment_api = AugerExperimentApi(self.ctx, self.project_api)
        experiment_api.create(data_set_name)
        self.ctx.log(
            'Created Experiment %s ' % experiment_api.object_name)

        experiment_session_id = experiment_api.run()
        self.ctx.log(
            'Started Experiment %s training.' % experiment_api.object_name)

        AugerConfig(self.ctx).set_experiment(
            experiment_api.object_name, experiment_session_id)
