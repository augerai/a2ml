import json
import sys
import traceback

from a2ml.api.auger.base import AugerBase
from a2ml.api.auger.hub.project import AugerProjectApi
from a2ml.api.auger.hub.experiment import AugerExperimentApi
from a2ml.api.auger.hub.project_file import AugerProjectFileApi
from a2ml.api.auger.hub.org import AugerOrganizationApi

class AugerTrain(AugerBase):
    """Train you Model on Auger."""
    def __init__(self, ctx):
        super(AugerTrain, self).__init__(ctx)
        self.ctx = ctx

    def train(self):
        try:
            # verify avalability of auger credentials
            self.credentials.verify()

            data_source = self._get_data_source()

            self.start_project()

            # print('Projects:')
            # project_api = AugerProjectApi(
            #     self.hub_client, self.org_id)
            # for item in iter(project_api.list()):
            #     print(item.get('name'))
            #
            # print('Project properties:')
            # project_api = AugerProjectApi(
            #     self.hub_client, self.org_id, 'cli-test-1')
            # project_api = project_api.properties()
            # print(json.dumps(project_api, indent = 2))

            # print('Experiments:')
            # experiment_api = AugerExperimentApi(
            #     self.hub_client, self.project_id)
            # for item in iter(experiment_api.list()):
            #     print(item.get('name'))
            #
            # print('Experiment:')
            # experiment_api = AugerExperimentApi(
            #     self.hub_client, self.project_id,
            #     '1209-dataset_8_liver-disorders.arff')
            # experiment_api = experiment_api.properties()
            # print(json.dumps(experiment_api, indent = 2))

            # print('Project File:')
            # project_file_api = AugerProjectFileApi(
            #     self.hub_client, self.project_id,
            #     'dataset_8_liver-disorders.arff')
            # data_source = project_file_api.properties()
            # print(json.dumps(data_source, indent = 2))

        except Exception as exc:
            # TODO refactor into reusable exception handler
            # with comprehensible user output
            traceback.print_stack()
            traceback.print_exc()
            self.ctx.log(str(exc))

    def _get_data_source(self):
        return None
