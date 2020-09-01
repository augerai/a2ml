import os
import csv

from ..cloud.pipeline import AugerPipelineApi
from .predict import ModelPredict
from a2ml.api.utils import fsclient

class ModelActual():
    """Predict using deployed Auger Model."""

    def __init__(self, ctx):
        super(ModelActual, self).__init__()
        self.ctx = ctx

    def execute(self, model_id, filename, actual_records, actuals_at):
        records, features, file_url, is_pandas_df = ModelPredict(self.ctx)._process_input(filename, actual_records, 
            columns=['prediction_id', 'actual'])
        pipeline_api = AugerPipelineApi(self.ctx, None, model_id)

        return pipeline_api.actual(records, actuals_at, file_url)
