from a2ml.api.auger.hub.base import AugerBaseApi


class AugerTrialApi(AugerBaseApi):
    """Wrapper around HubApi for Auger Trial."""

    def __init__(self, hub_client,
        experiment_session_api, trial_name=None, trial_id=None):
        super(AugerTrialApi, self).__init__(
            hub_client, experiment_session_api, trial_name, trial_id)
