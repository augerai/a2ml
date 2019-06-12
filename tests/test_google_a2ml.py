
import os
from a2ml.api.a2ml import A2ML
from a2ml.api.google.a2ml import GoogleA2ML
from a2ml.api.utils.context import pass_context

class TestGoogleA2ML():
    @pass_context
    def test_import_data():
        client = GoogleA2ML(ctx)
        result = client.import_data()
        assert(len(result.dataset_id)>0)

    @pass_context
    def test_train(ctx):
        client = GoogleA2ML(ctx)
        result = client.train(dataset_id,"RS",excluded.split(','),budget,metric)
        self.ctx.log("Train result: {}",format(result))
        assert(len(result.operation_name)>0)


