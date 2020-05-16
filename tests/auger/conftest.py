import logging
import shutil
import os
import json

import pytest
from a2ml.api.utils.context import Context
from a2ml.api.auger.impl.cloud.rest_api import RestApi

# from click.testing import CliRunner

#from auger.api.credentials import Credentials
#from auger.api.cloud.rest_api import RestApi

TEST_CREDENTIALS = {
    'username': 'test_user',
    'organization': 'auger',
    'api_url': 'https://example.com',
    'token': 'fake_token',
}

# @pytest.fixture
# def runner():
#     return CliRunner()


# @pytest.fixture(scope="function")
# def isolated(runner):
#     with runner.isolated_filesystem():
#         yield runner


@pytest.fixture
def log(caplog):
    caplog.set_level(logging.INFO)
    return caplog


@pytest.fixture
def project(isolated):
    source = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', 'fixtures',
        'cli-integration-test')
    shutil.copytree(source, './test_project')
    os.chdir('test_project')


@pytest.fixture
def ctx(project):
    ctx = Context(debug = False)
    ctx.config.set('providers', ["auger"])
    ctx.config.set('experiment/name', 'iris-1.csv-experiment')
    ctx.config.set('dataset', 'iris.csv')

    return ctx

@pytest.fixture
def ctx_api():
    # load config(s) from the test app
    ctx = Context(debug = True)
    ctx.config.set('providers', ["auger"])
    ctx.rest_api = RestApi('api_url', 'token')
    return ctx

@pytest.fixture
def authenticated(monkeypatch, isolated):
    monkeypatch.setenv("AUGER_CREDENTIALS", json.dumps(TEST_CREDENTIALS))
    #monkeypatch.setenv("AUGER_CREDENTIALS_PATH", os.getcwd())


@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    def request(*args, **kwargs):
        print("CALLED HubApiClient.request(", args, kwargs, ")")
        raise Exception("No way further")
        return {}
    monkeypatch.setattr('auger.hub_api_client.HubApiClient.request', request)

# import os
# import shutil
# import logging
# from click.testing import CliRunner
# from a2ml.api.utils.context import Context
# from a2ml.api.auger.impl.rest_api import RestApi


# @pytest.fixture
# def ctx():
#     # load config(s) from the test app
#     ctx = Context()
#     ctx.rest_api = RestApi('api_url', 'token')
#     return ctx

# @pytest.fixture
# def runner():
#     return CliRunner()

# @pytest.fixture(scope="function")
# def isolated(runner):
#     with runner.isolated_filesystem():
#         yield runner

# @pytest.fixture
# def log(caplog):
#     caplog.set_level(logging.INFO)
#     return caplog

# @pytest.fixture
# def project(isolated):
#     source = os.path.join(
#         os.path.dirname(os.path.abspath(__file__)), '..', 'fixtures',
#         'cli-integration-test')
#     shutil.copytree(source, './cli-integration-test')
#     os.chdir('cli-integration-test')
