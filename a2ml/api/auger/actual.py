import os
import csv

from .impl.cloud.pipeline import AugerPipelineApi
from .impl.decorators import error_handler, authenticated, with_project


class AugerActual(object):
    """Actual value for deployed Auger Pipeline."""

    def __init__(self, ctx):
        super(AugerActual, self).__init__(ctx)
        self.ctx.credentials = Credentials(ctx).load()
        self.ctx.rest_api = RestApi(
            self.ctx.credentials.api_url, self.ctx.credentials.token)
        
    @error_handler
    @authenticated
    @with_project(autocreate=False)
    def actual(self, filename, model_id):
        self.ctx.log('Sending actuals on data in %s' % filename)
        filename = os.path.abspath(filename)
        self._actual_to_cloud(filename, model_id)

    def _actual_to_cloud(self, filename, model_id):
        with open(filename) as f:
          a = [{k: v for k, v in row.items()} 
              for row in csv.DictReader(f, skipinitialspace=True)]

        pipeline_api = AugerPipelineApi(self.ctx, None, model_id)
        pipeline_api.actual(a)