import pytest
from a2ml.cmdl.cmdl import cmdl


class TestProjectCLI():
    def test_create_list_delete(self, runner, log, project):
        result = runner.invoke(cmdl, ['project', 'delete', 'cli-integration-test'])

        result = runner.invoke(cmdl, ['project', 'select', 'cli-integration-test'])
        assert log.messages[-1] == '[auger]  Selected Project cli-integration-test'

        result = runner.invoke(cmdl, ['project', 'create'])
        assert log.messages[-1] == '[auger]  Created Project cli-integration-test'

        result = runner.invoke(cmdl, ['project', 'list'])
        assert 'cli-integration-test' in str(log.messages)

        result = runner.invoke(cmdl, ['project', 'delete'])
        assert log.messages[-1] == '[auger]  Deleted Project cli-integration-test'
