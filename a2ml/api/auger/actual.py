import os
import csv
from a2ml.api.auger.base import AugerBase
from auger.api.cloud.pipeline import AugerPipelineApi



class AugerAcutal(AugerBase):
    """Actual value for deployed Auger Pipeline."""

    def __init__(self, ctx):
        super(AugerPredict, self).__init__(ctx)

    @AugerBase._error_handler
    def actual(self, filename, model_id):
        # verify avalability of auger credentials
        self.credentials.verify()

        self.ctx.log('Sending actuals on data in %s' % filename)
        filename = os.path.abspath(filename)
        self._actual_to_cloud(filename, model_id)

    def _actual_to_cloud(self, filename, model_id):
        with open(filename) as f:
          a = [{k: v for k, v in row.items()} 
              for row in csv.DictReader(f, skipinitialspace=True)]

        pipeline_api = AugerPipelineApi(self.ctx, None, model_id)
        pipeline_api.actual(a)