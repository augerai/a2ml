from .base import AugerBaseApi
from ..exceptions import AugerException


class AugerTrialApi(AugerBaseApi):
    """Auger Trial API."""

    def __init__(
        self, ctx, experiment_session_api,
        trial_name=None, trial_id=None):
        super(AugerTrialApi, self).__init__(
            ctx, experiment_session_api, trial_name, trial_id)
