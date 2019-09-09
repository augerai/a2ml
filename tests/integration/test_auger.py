import time
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

        while True:
            result = runner.invoke(cmdl, ['evaluate'])
            if log.messages[-1] in [
                '[auger]  Search is preprocessing data for training...',
                '[auger]  Search is in progress...']:
                time.sleep(10)
                continue
            elif log.messages[-1] == '[auger]  Search is completed.':
                model_id = log.messages[-3]\
                    .replace(' ', '').replace('[auger]','').split('|')[0]
                break
            else:
                assert log.messages[-1] == 'unknown message'

        print('model is: %s' % model_id)

        result = runner.invoke(cmdl, ['deploy', model_id, '--locally'])
        assert log.messages[-1] == '[auger]  Pulling docker image required to predict'

        result = runner.invoke(cmdl, ['predict', 'iris.csv', '-m', model_id, '--locally'])
        assert log.messages[-1].split('/')[-1] == 'iris_predicted.csv'

        result = runner.invoke(cmdl, ['project', 'delete', 'cli-integration-test'])
