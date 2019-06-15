
import os
from a2ml.api.a2ml import A2ML
from a2ml.api.google.a2ml import GoogleA2ML
from a2ml.api.utils.context import Context

class TestGoogleA2ML():
    def test_init(self):
        print("Current directory: {}".format(os.getcwd()))
        fulldir=os.getcwd()+"/tests/test_app"
        os.chdir(fulldir)
        # load config(s) from test app
        ctx = Context()

        a2ml = A2ML(ctx)
        assert len(a2ml.runner.providers)==3
        assert isinstance(a2ml.runner.providers[0], GoogleA2ML)
    
    def test_import_data(self): 
        print("Current directory: {}".format(os.getcwd()))

        # load config(s) from test app
        self.ctx = Context()

        a2ml = GoogleA2ML(self.ctx)
        result = a2ml.import_data()
        assert(len(result.dataset_id)>0)
    
    def test_train(self):
        ctx = Context()
        a2ml = GoogleA2ML(ctx)
        result = a2ml.train()
        print("Train result: {}",format(result))
 


