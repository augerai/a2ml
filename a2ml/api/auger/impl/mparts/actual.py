import os
import csv
from ..cloud.pipeline import AugerPipelineApi


class ModelActual():
    """Predict using deployed Auger Model."""

    def __init__(self, ctx):
        super(ModelActual, self).__init__()
        self.ctx = ctx

    def execute(self, filename, model_id):
        self.ctx.log('Sending actuals on data in %s' % filename)
        if filename and not fsclient.is_s3_path(filename):
            filename = os.path.abspath(filename)

        return self._actual_to_cloud(filename, model_id)

    def _actual_to_cloud(self, filename, model_id):
        with open(filename) as f:
          a = [{k: v for k, v in row.items()}
              for row in csv.DictReader(f, skipinitialspace=True)]

        pipeline_api = AugerPipelineApi(self.ctx, None, model_id)
        return pipeline_api.actual(a)
