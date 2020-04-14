import os
import pytest
import shutil
import logging
import json

from click.testing import CliRunner
from a2ml.api.utils.context import Context


@pytest.fixture
def ctx():
    # load config(s) from the test app
    return Context(debug=True)

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture(scope="function")
def isolated(runner):
    with runner.isolated_filesystem():
        yield runner

@pytest.fixture
def log(caplog):
    caplog.set_level(logging.INFO)
    return caplog

@pytest.fixture
def project(isolated):
    source = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'fixtures',
        'cli-integration-test')
    shutil.copytree(source, './cli-integration-test')
    os.chdir('cli-integration-test')

TEST_AUGER_CREDENTIALS = {
    'username': 'test_user',
    'organization': 'auger',
    'api_url': 'https://example.com',
    'token': 'fake_token',
}

@pytest.fixture
def auger_authenticated(monkeypatch, isolated):
    monkeypatch.setenv("AUGER_CREDENTIALS", json.dumps(TEST_AUGER_CREDENTIALS))
    #monkeypatch.setenv("AUGER_CREDENTIALS_PATH", os.getcwd())
