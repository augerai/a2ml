import os
from a2ml.api.a2ml import A2ML
from a2ml.api.auger.a2ml import AugerA2ML
from a2ml.api.google.a2ml import GoogleA2ML
from a2ml.api.utils.context import Context


class TestFacade(object):

    def test_init_a2ml(self):
        # run test in context of the test app
        os.chdir('tests/test_app')
        # load config(s) from test app
        ctx = Context()
        assert ctx.config['config'].providers == 'auger'
        a2ml = A2ML(ctx)
        assert len(a2ml.runner.providers) == 1
        assert isinstance(a2ml.runner.providers[0], AugerA2ML)
        # modify config on the fly
        ctx.config['config'].providers = ['auger','google']
        a2ml = A2ML(ctx)
        assert len(a2ml.runner.providers) == 2
        assert isinstance(a2ml.runner.providers[0], AugerA2ML)
        assert isinstance(a2ml.runner.providers[1], GoogleA2ML)
