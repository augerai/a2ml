import os
import csv

from ..cloud.pipeline import AugerPipelineApi

class ModelDeleteActual():
    """Predict using deployed Auger Model."""

    def __init__(self, ctx):
        super(ModelDeleteActual, self).__init__()
        self.ctx = ctx

    def execute(self, model_id, with_predictions, begin_date, end_date):
        pipeline_api = AugerPipelineApi(self.ctx, None, model_id)

        return pipeline_api.delete_actuals(with_predictions, begin_date, end_date)
