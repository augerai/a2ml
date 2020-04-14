import os
import pytest
from a2ml.api.azure.a2ml import AzureA2ML
from a2ml.api.utils.context import Context


class TestAzureA2ML():

    @pytest.mark.skip(reason='make it work first')
    def test_init(self):
        print("Current directory: {}".format(os.getcwd()))
        fulldir = os.getcwd() + "/tests/test_app"
        os.chdir(fulldir)

    @pytest.mark.skip(reason='make it work first')
    def test_import_data(self):
        print("Current directory: {}".format(os.getcwd()))
        self.ctx = Context()
        print("Project name: {}".format(self.ctx.config.get('name')))
        a2ml = AzureA2ML(self.ctx.copy('azure'))
        a2ml.import_data()
