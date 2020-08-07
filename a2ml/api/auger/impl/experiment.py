from datetime import datetime

from .cloud.experiment import AugerExperimentApi
from .exceptions import AugerException
from .cloud.experiment_session import AugerExperimentSessionApi


class Experiment(AugerExperimentApi):
    """Auger Cloud Experiments(s) management"""

    def __init__(self, ctx, dataset, experiment_name=None):
        super(Experiment, self).__init__(
            ctx, dataset.project, experiment_name)
        self.dataset = dataset

    def list(self):
        # data_set_id = self.dataset.oid
        # filter_by_dataset = \
        #     lambda exp: exp.get('project_file_id') == data_set_id
        # return (e for e in super().list() if filter_by_dataset(e))
        return super().list()

    def start(self):
        if self.dataset is None:
            raise AugerException(
                'DataSet is required to start Experiment...')

        if not self.dataset.is_exists:
            raise AugerException('Can\'t find DataSet on Auger Cloud...')

        if self.object_name and self.is_exists:
            data_set_id = self.dataset.oid
            experiment_data_set = self.properties().get('project_file_id')
            if data_set_id != experiment_data_set:
                self.object_id = None
                self.object_name = None
                self.ctx.log('Current experiment setup with different DataSet. '
                    'Will create new Experimet...')

        self.dataset.project.start()

        if (self.object_name is None) or (not self.is_exists):
            self.create(self.dataset.name)
            self.ctx.log('Created Experiment %s ' % self.name)

        experiment_session_id = self.run()
        self.ctx.log('Started Experiment %s search...' % self.name)

        return self.name, experiment_session_id

    def stop(self, run_id=None):
        if run_id is None:
            run_id = self._get_latest_run()
            
        session_api = AugerExperimentSessionApi(
            self.ctx, None, None, run_id)
        return session_api.interrupt()

    def leaderboard(self, run_id=None):
        if run_id is None:
            run_id = self._get_latest_run()

        if run_id is None:
            return None, None, None
        else:
            session_api = AugerExperimentSessionApi(
                self.ctx, None, None, run_id)
            session_props = session_api.properties()
            status = session_props.get('status')
            errors = None
            if session_props.get('providers_data'):
                if session_props['providers_data'].get(self.ctx.get_name()):
                    errors = session_props['providers_data'][self.ctx.get_name()].get('errors')
            if not errors:
                errors = session_props.get('model_settings', {}).get('errors')

            return session_api.get_leaderboard(), status, run_id, \
                session_props.get('model_settings', {}).get('completed_evaluations', 0), errors
                
    def history(self):
        return AugerExperimentSessionApi(self.ctx, self).list()

    def _get_latest_run(self):
        latest = [None, None]
        for run in iter(self.history()):
            start_time = run.get('model_settings').get('start_time')
            if start_time:
                start_time = datetime.strptime(
                    start_time, '%Y-%m-%d %H:%M:%S.%f')
                if (latest[0] is None) or (latest[1] < start_time):
                    latest = [run.get('id'), start_time]
        return latest[0]

    def wait(self, run_id=None):
        if run_id is None:
            run_id = self._get_latest_run()

        if run_id is None:
            return None, None
        else:
            AugerExperimentSessionApi(
                self.ctx, self, None, run_id).wait_for_status([
                    'waiting', 'preprocess', 'started'])
