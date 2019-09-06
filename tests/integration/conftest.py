import os
import pytest
import shutil
import logging
from click.testing import CliRunner

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
        os.path.dirname(os.path.abspath(__file__)), '..', 'fixtures',
        'cli-integration-test')
    shutil.copytree(source, './cli-integration-test')
    os.chdir('cli-integration-test')
