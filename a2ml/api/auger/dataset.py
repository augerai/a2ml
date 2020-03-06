from auger.api.cloud.rest_api import RestApi
from auger.api.credentials import Credentials
from auger.cli.commands.impl.datasetcmd import DataSetCmd

class AugerDataset(DataSetCmd):

    def __init__(self, ctx):
        super(AugerDataset, self).__init__(ctx)
        self.ctx.credentials = Credentials(ctx).load()
        self.ctx.rest_api = RestApi(
            self.ctx.credentials.api_url, self.ctx.credentials.token)
