import time

from .base import AugerBaseApi
from .trial import AugerTrialApi
from ..exceptions import AugerException

class AugerExperimentSessionApi(AugerBaseApi):
    """Auger Experiment Api."""

    def __init__(self, ctx, experiment_api=None,
        session_name=None, session_id=None):
        super(AugerExperimentSessionApi, self).__init__(
            ctx, experiment_api, session_name, session_id)

    def list(self, params=None):
        params = {} if params is None else params
        params['project_id'] = self.parent_api.parent_api.oid
        return super().list(params)

    def run(self):
        try:
            return self._call_update({'id': self.object_id, 'status': 'preprocess'})
            # return self.rest_api.call(
            #     'update_experiment_session',
            #     {'id': self.object_id, 'status': 'preprocess'})
        except Exception as e:
            self.ctx.log(
                'Start experiment session failed. Try one more time ...: %s' % (e))

            #Try one more time
            time.sleep(60)
            return self._call_update({'id': self.object_id, 'status': 'preprocess'})
            # return self.rest_api.call(
            #     'update_experiment_session',
            #     {'id': self.object_id, 'status': 'preprocess'})

        # self.wait_for_status(['waiting', 'preprocess', 'started'])

    def interrupt(self):
        try:
            status = self.status()
            if status in ['waiting', 'preprocess', 'started']:
                self.rest_api.call(
                    'update_experiment_session',
                    {'id': self.object_id, 'status': 'interrupted'})
                return True
        except Exception as e:
            if 'Event \'interrupted\' cannot transition' not in str(e):
                raise
        return False

    def create(self):
        evaluation_options, model_type, dataset_statistics = \
            self.parent_api.get_experiment_settings()
        return self._call_create({
            'experiment_id': self.parent_api.object_id,
            'model_settings': evaluation_options,
            'dataset_statistics': dataset_statistics,
            'model_type': model_type})

    def get_leaderboard(self):
        #TODO: create leaderboard same way as in auger-ml
        trial_api = AugerTrialApi(self.ctx, self)
        leaderboard, score_name = [], None
        for item in iter(trial_api.list()):
            score_name = item.get('score_name')
            l_item = {
                'model id': item.get('id'),
                'algorithm': item.get('hyperparameter').\
                    get('algorithm_name').split('.')[-1],
                item.get('score_name'):\
                    '{0:.4f}'.format(item.get('score_value'))
            }
            review_metric = self.ctx.config.get('review/metric')
            if review_metric == 'roi':
                review_metric = 'mda'
            if review_metric:
                l_item[review_metric] = \
                    '{0:.4f}'.format(item.get('raw_data', {}).get('all_scores', {}).get(review_metric, 0.0))

            l_item['score'] = float(item.get('score_value'))
            l_item['fold_scores'] = []
            for item in item.get('raw_data', {}).get('fold_scores', []):
                l_item['fold_scores'].append('{0:.4f}'.format(item))

            leaderboard.append(l_item)

        if score_name:
            leaderboard.sort(key=lambda t: t['score'], reverse=False)
        
        for item in leaderboard:
            del item['score']
                
        return leaderboard

    def update_settings(self):
        from .experiment import AugerExperimentApi

        if not self.ctx.config.get('experiment'):
            self.ctx.log("Config does not contain experiment section. Do not update Review retrain options")
            return

        session_props = self.properties()
        props = session_props.get('model_settings',{}).get('evaluation_options')
        config_props = AugerExperimentApi.get_experiment_options(self.ctx.config)
        update_props = {}
        for name, value in config_props.items():
            if not name in props or props.get(name) != config_props.get(name):
                update_props[name] = value

        if update_props:
            self.ctx.log("Updating Review retrain options: %s"%update_props)
            model_settings = session_props['model_settings']
            for name, value in update_props.items():
                model_settings['evaluation_options'][name] = value

            self._call_update({'id': self.object_id, 'model_settings': model_settings})
