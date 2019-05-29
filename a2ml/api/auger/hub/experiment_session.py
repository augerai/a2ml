from a2ml.api.auger.hub.base import AugerBaseApi
from a2ml.api.auger.hub.trial import AugerTrialApi


class AugerExperimentSessionApi(AugerBaseApi):
    """Wrapper around HubApi for Auger Experiment Api."""

    def __init__(self,
        hub_client, experiment_api,
        session_name=None, session_id=None):
        super(AugerExperimentSessionApi, self).__init__(
            hub_client, experiment_api, session_name, session_id)

    def list(self, params=None):
        return super().list({
            'project_id': self.parent_api.parent_api.object_id})

    def run(self):
        return self.hub_client.call_hub_api(
            'update_experiment_session',
            {'id': self.object_id, 'status': 'preprocess'})
        # self.wait_for_status(['waiting', 'preprocess', 'started'])

    def create(self):
        evaluation_options, model_type = \
            self.parent_api.get_experiment_settings()
        return self._call_create({
            'experiment_id': self.parent_api.object_id,
            'model_settings': evaluation_options,
            'model_type': model_type})

    def get_leaderboard(self):
        trial_api = AugerTrialApi(self.hub_client, self)
        leaderboard, score_name = [], None
        for item in iter(trial_api.list()):
            score_name = item.get('score_name')
            leaderboard.append({
                'id': item.get('id'),
                item.get('score_name'):\
                    '{0:.2f}'.format(item.get('score_value')),
                'algorithm': item.get('hyperparameter').\
                    get('algorithm_name').split('.')[-1]})
        if score_name:
            leaderboard.sort(key=lambda t: t[score_name], reverse=False)
        return leaderboard
