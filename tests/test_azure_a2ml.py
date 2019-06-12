from a2ml.api.azure.a2ml import AzureA2ML
from a2ml.api.utils.context import pass_context

@pass_context
def test_import_data():
    client=AzureA2ML(ctx)
    client.import_data()
    