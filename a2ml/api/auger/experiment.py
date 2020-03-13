from auger.api.cloud.rest_api import RestApi
from auger.api.credentials import Credentials
from auger.cli.commands.impl.experimentcmd import ExperimentCmd

class AugerExperiment(ExperimentCmd):

    def __init__(self, ctx):
        super(AugerExperiment, self).__init__(ctx)
        self.ctx.credentials = Credentials(ctx).load()
        self.ctx.rest_api = RestApi(
            self.ctx.credentials.api_url, self.ctx.credentials.token)
