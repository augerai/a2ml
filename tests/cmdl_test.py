import os
from pathlib import Path

from click.testing import CliRunner

from a2ml.cmdl.cmdl import cmdl

class TestCmdl(object):

    def test_empty_a2ml(self):
        runner = CliRunner()
        result = runner.invoke(cmdl)
        assert result.exit_code == 0
        assert 'A2ML command line interface.' in result.output
        assert 'auth      Authenticate with AutoML provider.' in result.output
        assert 'deploy    Deploy trained model.' in result.output
        assert 'evaluate  Evaluate models after training.' in result.output
        assert 'import    Import data for training.' in result.output
        assert 'new       Create new A2ML project.' in result.output
        assert 'predict   Predict with deployed model.' in result.output
        assert 'review    Review specified model info.' in result.output
        assert 'train     Train the model.' in result.output


class TestNewCmd(object):
    PROJECT_NAME = 'new_project'

    def setup_method(self):
        self.runner = CliRunner()

    def test_new_requires_project_name(self):
        result = self.runner.invoke(cmdl, ['new'])
        assert 'Error: Missing argument "PROJECT_NAME"' in result.output
        assert result.exit_code == 2

    def test_new_creates_valid_structure(self):
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cmdl, ['new', self.PROJECT_NAME])
            assert result.exit_code == 0
            assert Path(self.PROJECT_NAME).exists()
            for filename in ('google.yaml', 'azure.yaml', 'config.yaml', 'auger.yaml'):
                file = Path(os.path.join(self.PROJECT_NAME, filename))
                assert file.exists()

    def test_new_already_existing(self):
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cmdl, ['new', self.PROJECT_NAME])
            assert result.exit_code == 0
            result = self.runner.invoke(cmdl, ['new', self.PROJECT_NAME])
            # FIXME: this must fail, but it still doesn't
            assert result.exit_code != 0
