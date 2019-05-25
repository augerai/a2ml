from a2ml.api.auger.hub.base import AugerBaseApi


class AugerExperimentApi(AugerBaseApi):
    """Wrapper around HubApi for Auger Experiment Api."""

    def __init__(self,
        hub_client, project_api, experiment_name=None, experiment_id=None):
        super(AugerExperimentApi, self).__init__(
            hub_client, project_api, experiment_name, experiment_id)
        assert project_api is not None, 'Project must be set for Experiment'

    def create(self):
        pass
