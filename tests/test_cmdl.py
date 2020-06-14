import os
from pathlib import Path
from a2ml.cmdl.cmdl import cmdl


class TestCmdl(object):

    def test_empty_a2ml(self, runner):
        result = runner.invoke(cmdl)
        assert result.exit_code == 0
        assert 'A2ML command line interface.' in result.output
        assert 'auth        Authenticate with AutoML provider.' in result.output
        assert 'deploy      Deploy trained model.' in result.output
        assert 'evaluate    Evaluate models after training.' in result.output
        assert 'import      Import data for training.' in result.output
        assert 'new         Create new A2ML project.' in result.output
        assert 'predict     Predict with deployed model.' in result.output
        assert 'train       Train the model.' in result.output


class TestNewCmd(object):
    PROJECT_NAME = 'new_project'

    def test_new_requires_project_name(self, runner):
        result = runner.invoke(cmdl, ['new'])
        assert 'Error: Missing argument' in result.output
        assert 'PROJECT' in result.output
        assert result.exit_code == 2

    def test_new_creates_valid_structure(self, runner):
        with runner.isolated_filesystem():
            result = runner.invoke(cmdl, ['new', self.PROJECT_NAME])
            assert result.exit_code == 0
            assert Path(self.PROJECT_NAME).exists()
            for filename in ('google.yaml', 'azure.yaml', 'config.yaml', 'auger.yaml'):
                file = Path(os.path.join(self.PROJECT_NAME, filename))
                assert file.exists()

    def test_new_already_existing(self, runner, log):
        with runner.isolated_filesystem():
            result = runner.invoke(cmdl, ['new', self.PROJECT_NAME])
            assert result.exit_code == 0
            result = runner.invoke(cmdl, ['new', self.PROJECT_NAME])
            assert result.exit_code == 0
            assert (log.messages[-1] ==
                "[config] Can't create 'new_project'. Folder already exists.")
