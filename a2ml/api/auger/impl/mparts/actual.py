import os
import csv

from ..cloud.pipeline import AugerPipelineApi
from a2ml.api.utils import fsclient

class ModelActual():
    """Predict using deployed Auger Model."""

    def __init__(self, ctx):
        super(ModelActual, self).__init__()
        self.ctx = ctx

    def execute(self, model_id, filename, actual_records, actuals_at):
        if filename:
            self.ctx.log('Sending actuals on data in %s' % filename)
            if filename and not fsclient.is_s3_path(filename):
                filename = os.path.abspath(filename)

            return self._file_actual_to_cloud(filename, model_id, actuals_at)
        else:
            return self._actuals_to_cloud(actual_records, model_id, actuals_at)

    def _file_actual_to_cloud(self, filename, model_id, actuals_at):
        with open(filename) as f:
          a = [{k: v for k, v in row.items()}
              for row in csv.DictReader(f, skipinitialspace=True)]

        pipeline_api = AugerPipelineApi(self.ctx, None, model_id)
        return pipeline_api.actual(a, actuals_at)

    def _actuals_to_cloud(self, actual_records, model_id, actuals_at):
        pipeline_api = AugerPipelineApi(self.ctx, None, model_id)
        return pipeline_api.actual(actual_records, actuals_at)
