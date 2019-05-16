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
        assert 'new       Create new A2ML experiment.' in result.output
        assert 'predict   Predict with deployed model.' in result.output
        assert 'review    Review specified model info.' in result.output
        assert 'train     Train the model.' in result.output
