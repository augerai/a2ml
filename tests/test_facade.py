import pytest
from a2ml.api.a2ml import A2ML
from a2ml.api.auger.a2ml import AugerA2ML
from a2ml.api.google.a2ml import GoogleA2ML

from .utils.mock_helpers import MockHelpers


class TestFacade(object):

    @pytest.fixture
    def mock_inits(self, monkeypatch):
        MockHelpers.pass_method(AugerA2ML, "__init__", monkeypatch)
        MockHelpers.pass_method(GoogleA2ML, "__init__", monkeypatch)

    def test_init_a2ml(self, project, ctx, monkeypatch):
        init_auger = MockHelpers.count_calls(
            AugerA2ML, "__init__", monkeypatch)
        init_google = MockHelpers.count_calls(
            GoogleA2ML, "__init__", monkeypatch)
        ctx.config.set('providers', 'auger')
        a2ml = A2ML(ctx)
        assert len(a2ml.runner.providers) == 1
        assert isinstance(a2ml.runner.providers['auger'], AugerA2ML)
        assert init_auger.times == 1
        assert init_google.times == 0
        # modify config on the fly
        ctx.config.set('providers', ['auger','google'])
        init_auger.reset()
        init_google.reset()
        a2ml = A2ML(ctx)
        assert len(a2ml.runner.providers) == 2
        assert isinstance(a2ml.runner.providers['auger'], AugerA2ML)
        assert isinstance(a2ml.runner.providers['google'], GoogleA2ML)
        assert init_auger.times == 1
        assert init_google.times == 1

    def test_calling_operations(self, project, ctx, mock_inits, monkeypatch):
        def test_operation(operation, args):
            auger_operation = MockHelpers.called_with(
                AugerA2ML, operation, monkeypatch)
            google_operation = MockHelpers.called_with(
                GoogleA2ML, operation, monkeypatch)
            #run operation for a single provider
            ctx.config.set('providers', ['auger'])
            a2ml = A2ML(ctx)
            getattr(a2ml, operation)(*args)
            assert auger_operation.times == 1
            assert google_operation.times == 0
            for arg in range(len(args)):
                assert auger_operation.args[arg+1] == args[arg]
            #run operation for multiple providers
            if operation != 'deploy' and operation != 'predict':
                ctx.config.set('providers', ['auger','google'])
                auger_operation.reset()
                google_operation.reset()
                a2ml = A2ML(ctx)
                getattr(a2ml, operation)(*args)
                assert auger_operation.times == 1
                assert google_operation.times == 1
                for arg in range(len(args)):
                    assert auger_operation.args[arg+1] == args[arg]
                    assert google_operation.args[arg+1] == args[arg]
        ops = {
            'import_data': [],
            'train': [],
            'evaluate': [],
            'deploy': ['some_model_id', True],
            #'predict': ['some_model_id', 'some_csv', 0.5, True]
        }
        for opname, args in ops.items():
            test_operation(opname, args)
