from auger.api.dataset import DataSet
from auger.cli.utils.decorators import \
    error_handler, authenticated, with_project
from auger.api.cloud.rest_api import RestApi
from auger.api.credentials import Credentials
from a2ml.api.auger.config import AugerConfig


class AugerImport(object):
    """Import data into Auger."""

    def __init__(self, ctx):
        super(AugerImport, self).__init__()
        self.ctx = ctx
        self.ctx.credentials = Credentials(ctx).load()
        self.ctx.rest_api = RestApi(
            self.ctx.credentials.api_url, self.ctx.credentials.token)

    @error_handler
    @authenticated
    @with_project(autocreate=True)
    def import_data(self, project):
        source = self.ctx.config.get('source', None)
        dataset = DataSet(self.ctx, project).create(source)
        AugerConfig(self.ctx).set_data_set(dataset.name)
        self.ctx.log('Created DataSet %s' % dataset.name)
        return {'dataset': dataset.name}
