from a2ml.api.azure.a2ml import AzureA2ML
from a2ml.api.utils.context import Context

class TestAzureA2ML():

    def init(self):
        print("Current directory: {}".format(os.getcwd()))
        fulldir=os.getcwd()+"/tests/test_app"
        os.chdir(fulldir)

    def test_import_data(self):
        ctx = Context()
        #print("Name of model: {}".format(ctx.config['config'].name))
        a2ml=AzureA2ML(ctx)
        a2ml.import_data()
    