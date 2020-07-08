import os

from a2ml.cmdl.cmdl import cmdl
from a2ml.api.utils.context import Context

class TestNewCommand():

    def test_minimal_arguments_successfull_creation(self, runner, isolated):
        # successful status
        result = runner.invoke(cmdl, ['new', 'test_project'])
        assert result.exit_code == 0

        # directory created
        target_dir = os.path.join(os.getcwd(), 'test_project')
        assert os.path.exists(target_dir) and os.path.isdir(target_dir)

        # config file exists
        config_file = os.path.join(target_dir, 'auger.yaml')
        assert os.path.exists(config_file)

        # config contains proper data
        config = Context(path=target_dir).config
        assert config.get('name', '') == 'test_project'

    def test_project_with_given_name_already_exists(self, runner, log, isolated):
        os.chdir('..')
        runner.invoke(cmdl, ['new', 'test_project'])
        result = runner.invoke(cmdl, ['new', 'test_project'])
        #assert result.exit_code != 0
        assert (log.records[-1].message ==
                "[config] Can't create 'test_project'. Folder already exists.")

    def test_nested_project_forbidden(self, runner, log, isolated):
        result = runner.invoke(cmdl, ['new', 'test_project'])
        #assert result.exit_code != 0
        assert (log.records[-1].message ==
                "[config] To build your model, please do:"
                " cd test_project && a2ml import && a2ml train")

    def test_full_set_of_arguments(self, log, runner, isolated, project):
        os.chdir('..')
        result = runner.invoke(
            cmdl, [
                'new', 'new_project',
                '--model-type', 'regression',
                '--target', 'target_column',
                '--source', 'cli-integration-test/iris.csv'])

        assert result.exit_code == 0
        
        target_dir = os.path.join(os.getcwd(), 'new_project')
        config = Context(path=target_dir).config

        assert config.get('model_type', '') == 'regression'
        assert config.get('target', '') == 'target_column'
        assert config.get('source', '') == os.path.join(
            os.getcwd(), 'cli-integration-test', 'iris.csv')

    def test_bad_source(self, log, runner, isolated):
        result = runner.invoke(
            cmdl, ['new', 'test_project', '--source', 'not_existing_file.csv'])
        #assert result.exit_code != 0
        assert log.messages[-1].startswith("[config] Can't find file to import:")

    def test_source_wrong_extension(self, log, runner, isolated):
        result = runner.invoke(
            cmdl, ['new', 'test_project', '--source', 'file_with_wrong.extension'])
        #assert result.exit_code != 0
        assert log.messages[-1] ==\
             '[config] Source file has to be one of the supported fomats: .csv, .arff, .gz, .bz2, .zip, .xz, .json, .xls, .xlsx, .feather, .h5, .hdf5, .parquet'
