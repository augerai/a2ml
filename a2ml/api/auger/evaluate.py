from a2ml.api.auger.base import AugerBase
from auger.api.cloud.utils.exception import AugerException
from auger.api.cloud.experiment import AugerExperimentSessionApi
from auger.cli.utils.formatter import print_table


class AugerEvaluate(AugerBase):
    """Evaluate you Model on Auger."""

    def __init__(self, ctx):
        super(AugerEvaluate, self).__init__(ctx)

    @AugerBase._error_handler
    def evaluate(self):
        # verify avalability of auger credentials
        self.credentials.verify()

        experiment_session_id = self.ctx.config['auger'].get(
            'experiment/experiment_session_id')
        if experiment_session_id is None:
            raise AugerException('Can\'t find previously run experiments'
                ' (auger.yaml/experiment/experiment_session_id option).')

        experiment_session_api = AugerExperimentSessionApi(
            self.ctx, None, None, experiment_session_id)
        leaderboard = experiment_session_api.get_leaderboard()
        if leaderboard is None:
            raise AugerException('No leaderboard was found...')
        print_table(self.ctx.log,leaderboard[::-1])

        status = experiment_session_api.properties().get('status')
        messages = {
            'preprocess': 'Search is preprocessing data for training...',
            'started': 'Search is in progress...',
            'completed': 'Search is completed.'
        }
        message = messages.get(status, None)
        if message:
            self.ctx.log(message)
        else:
            self.ctx.log('Search status is %s' % status)
