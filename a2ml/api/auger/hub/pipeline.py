from a2ml.api.auger.hub.base import AugerBaseApi


class AugerPipelineApi(AugerBaseApi):
    """Wrapper around HubApi for Auger Pipeline."""

    def __init__(
        self, experiment_api,
        pipeline_name=None, pipeline_id=None):
        super(AugerPipelineApi, self).__init__(
            experiment_api, pipeline_name, pipeline_id)

    def create(self, trial_id):
        return self._call_create({'trial_id': trial_id},
            ['creating_files', 'packaging', 'deploying'])
