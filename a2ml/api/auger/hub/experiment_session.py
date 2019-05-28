from a2ml.api.auger.hub.base import AugerBaseApi


class AugerExperimentSessionApi(AugerBaseApi):
    """Wrapper around HubApi for Auger Experiment Api."""

    def __init__(self,
        hub_client, experiment_api,
        session_name=None, session_id=None):
        super(AugerExperimentSessionApi, self).__init__(
            hub_client, experiment_api, session_name, session_id)
        assert experiment_api is not None, \
            'Experiment must be set for Experiment Session'

    def list(self, params=None):
        return super().list({
            'project_id': self.parent_api.parent_api.object_id})

    def run(self):
        return self.hub_client.call_hub_api(
            'update_experiment_session',
            {'id': self.object_id, 'status': 'preprocess'})

    def create(self):
        evaluation_options, model_type = \
            self.parent_api.get_experiment_settings()
        return self._call_create({
            'experiment_id': self.parent_api.object_id,
            'model_settings': evaluation_options,
            'model_type': model_type})
