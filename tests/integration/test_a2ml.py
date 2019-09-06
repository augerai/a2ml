import pytest
from a2ml.cmdl.cmdl import cmdl


class TestA2mlCLI():
    def test_import_train_evaluate_deploy_predict(self, runner, log, project):
        result = runner.invoke(cmdl, ['project', 'delete', 'cli-integration-test'])

        result = runner.invoke(cmdl, ['import'])
        assert log.messages[-2] == '[auger]  Created DataSet iris.csv on Auger Cloud.'
        assert log.messages[-1] == '[auger]  DataSet name stored in auger.yaml/dataset'

        result = runner.invoke(cmdl, ['dataset', 'list'])
        assert log.messages[-2] == '[auger]  [x] iris.csv'
        assert log.messages[-1] == '[auger]  1 DataSet(s) listed'

        result = runner.invoke(cmdl, ['train'])
        assert log.messages[-2] == '[auger]  Created Experiment iris.csv-experiment '
        assert log.messages[-1] == '[auger]  Started Experiment iris.csv-experiment training.'
