from auger.api.cloud.rest_api import RestApi
from auger.api.credentials import Credentials
from auger.cli.commands.cmd_project import ProjectCmd

class AugerProject(ProjectCmd):

    def __init__(self, ctx):
        super(AugerProject, self).__init__(ctx)
        self.ctx.credentials = Credentials(ctx).load()
        self.ctx.rest_api = RestApi(
            self.ctx.credentials.api_url, self.ctx.credentials.token, debug=self.ctx.debug)
