import os
import pytest

from .utils import interceptor, object_status_chain, ORGANIZATIONS, PROJECTS
from a2ml.api.auger.model import AugerModel

class TestModel():
    def test_deploy_locally(self, log, project, ctx, authenticated, monkeypatch):
        PAYLOAD = {
            'get_organizations': ORGANIZATIONS,
            'get_projects': PROJECTS,
        }
        interceptor(PAYLOAD, monkeypatch)
        object_status_chain(['undeployed', 'deployed', 'deploying', 'running'], monkeypatch)
        monkeypatch.setattr('a2ml.api.auger.impl.mparts.deploy.ModelDeploy._docker_pull_image', lambda self: 'experimental')
        monkeypatch.setattr('a2ml.api.auger.impl.mparts.deploy.ModelDeploy._start_project', lambda self: None)
        os.remove('models/model-87C81FE615DE46D.zip')
        # FIXME: let AugerPipelineFileApi do it's work
        monkeypatch.setattr('a2ml.api.auger.impl.cloud.pipeline_file.AugerPipelineFileApi.create', lambda self, model_id: {'signed_s3_model_path': 'None'})
        monkeypatch.setattr('a2ml.api.auger.impl.cloud.pipeline_file.AugerPipelineFileApi.download', lambda *a, **kw: 'models/export-%s.zip' % '87C81FE615DE46D')

        result = AugerModel(ctx).deploy('87C81FE615DE46D', locally=True)
        assert result['model_id'] == '87C81FE615DE46D'

    @pytest.mark.skip(reason="not implemented on server-side currently")
    def test_deploy_remoteley(self, log, project, ctx, authenticated, monkeypatch):
        result = runner.invoke(cli, ['model', 'deploy'])
        pass

    def test_predict_locally(self, log, project, ctx, authenticated, monkeypatch):
        PAYLOAD = {
            'get_organizations': ORGANIZATIONS,
            'get_projects': PROJECTS,
        }
        interceptor(PAYLOAD, monkeypatch)
        monkeypatch.setattr('subprocess.check_output', lambda *a, **kw: b'iris_predicted.csv')
        monkeypatch.setattr('subprocess.check_call', lambda *a, **kw: b'iris_predicted.csv')

        result = AugerModel(ctx).predict(filename='iris.csv', model_id='87C81FE615DE46D', 
            threshold=None, locally=True, data=None, columns=None)

        assert result.get('predicted')
        assert 'test_project/predictions/iris_predicted.csv' in result.get('predicted')


    @pytest.mark.skip(reason="not implemented on server-side currently")
    def test_predict_remoteley(self, log, project, ctx, authenticated, monkeypatch):
        result = runner.invoke(cli, ['model', 'predict', 'iris.csv'])
        pass

    @pytest.mark.skip(reason="not implemented on server-side currently")
    def test_actual_remoteley(self, log, project, ctx, authenticated, monkeypatch):
        result = runner.invoke(cli, ['model', 'actual', 'iris.csv'])
        pass
