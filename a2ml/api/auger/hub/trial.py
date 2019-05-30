from a2ml.api.auger.hub.base import AugerBaseApi


class AugerTrialApi(AugerBaseApi):
    """Wrapper around HubApi for Auger Trial."""

    def __init__(
        self, experiment_session_api,
        trial_name=None, trial_id=None):
        super(AugerTrialApi, self).__init__(
            experiment_session_api, trial_name, trial_id)
