import json
import sys

from a2ml.api.auger.base import AugerBase
from a2ml.api.auger.hub.utils.exception import AugerException
from a2ml.api.auger.hub.experiment import AugerExperimentSessionApi
from a2ml.api.utils.formatter import print_table


class AugerEvaluate(AugerBase):
    """Evaluate you Model on Auger."""
    def __init__(self, ctx):
        super(AugerEvaluate, self).__init__(ctx)
        self.ctx = ctx

    def evaluate(self):
        try:
            # verify avalability of auger credentials
            self.credentials.verify()

            # self.start_project()

            experiment_session_id = self.ctx.config['auger'].get(
                'experiment/experiment_session_id')
            if experiment_session_id is None:
                raise AugerException('Can\'t find previously run experiments'
                    ' (auger.yaml/experiment/experiment_session_id option).')

            experiment_session_api = AugerExperimentSessionApi(
                None, None, experiment_session_id)
            print_table(self.ctx.log, experiment_session_api.get_leaderboard())
            self.ctx.log('Search status is %s' % \
                experiment_session_api.properties().get('status'))

        except Exception as exc:
            # TODO refactor into reusable exception handler
            # with comprehensible user output
            import traceback
            traceback.print_exc()
            self.ctx.log(str(exc))
