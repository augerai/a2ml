from a2ml.api.azure.a2ml import AzureA2ML
from a2ml.api.utils.context import Context

import os 
class TestAzureA2ML():

    def test_init(self):
        print("Current directory: {}".format(os.getcwd()))
        fulldir=os.getcwd()+"/tests/test_app"
        os.chdir(fulldir)

    def test_import_data(self):
        print("Current directory: {}".format(os.getcwd()))
        self.ctx = Context()
        print("Project name: {}".format(self.ctx.config['config'].name))
        a2ml=AzureA2ML(self.ctx)
        a2ml.import_data()
    