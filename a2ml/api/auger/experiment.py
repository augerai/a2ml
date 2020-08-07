from .impl.cloud.rest_api import RestApi
from .impl.decorators import with_dataset
from a2ml.api.utils.decorators import error_handler, authenticated
from .impl.experiment import Experiment
from .impl.exceptions import AugerException
from a2ml.api.utils.formatter import print_table
from .credentials import Credentials
from .config import AugerConfig

class AugerExperiment(object):

    def __init__(self, ctx):
        self.ctx = ctx
        self.credentials = Credentials(ctx).load()
        self.ctx.rest_api = RestApi(
            self.credentials.api_url, self.credentials.token)

    @error_handler
    @authenticated
    @with_dataset
    def list(self, dataset):
        count = 0
        for exp in iter(Experiment(self.ctx, dataset).list()):
            self.ctx.log(exp.get('name'))
            count += 1
        self.ctx.log('%s Experiment(s) listed' % str(count))
        return {'experiments': Experiment(self.ctx, dataset).list()}

    @error_handler
    @authenticated
    @with_dataset
    def start(self, dataset):
        experiment_name = \
            self.ctx.config.get('experiment/name', None)
        experiment_name, session_id = \
            Experiment(self.ctx, dataset, experiment_name).start()
        AugerConfig(self.ctx).set_experiment(experiment_name, session_id)
        return {'experiment_name': experiment_name, 'session_id': session_id}

    @error_handler
    @authenticated
    @with_dataset
    def stop(self, dataset, run_id = None):
        name = self.ctx.config.get('experiment/name', None)
        if name is None:
            raise AugerException('Please specify Experiment name...')
        if run_id is None:
            run_id = self.ctx.config.get(
                'experiment/experiment_session_id', None)

        if Experiment(self.ctx, dataset, name).stop(run_id):
            self.ctx.log('Search is stopped...')
        else:
            self.ctx.log('Search is not running. Stop is ignored.')
        return {'stopped': name}

    @error_handler
    @authenticated
    @with_dataset
    def leaderboard(self, dataset, run_id = None):
        name = self.ctx.config.get('experiment/name', None)
        if name is None:
            raise AugerException('Please specify Experiment name...')
        if run_id is None:
            run_id = self.ctx.config.get(
                'experiment/experiment_session_id', None)
        leaderboard, status, run_id, trials_count, errors = Experiment(
            self.ctx, dataset, name).leaderboard(run_id)
        if leaderboard is None:
            raise AugerException('No leaderboard was found...')
        self.ctx.log('Leaderboard for Run %s' % run_id)
        leaderboard = leaderboard[::-1]
        leaderboard = leaderboard[:10]

        print_table(self.ctx.log, leaderboard)
        messages = {
            'preprocess': 'Search is preprocessing data for training...',
            'started': 'Search is in progress...',
            'completed': 'Search is completed.',
            'interrupted': 'Search was interrupted.',
            'error': 'Search was finished with error'
        }
        message = messages.get(status, None)

        result = {
            'run_id': run_id, 
            'leaderboard': leaderboard,
            'trials_count': trials_count,
            'status': status,
            'provider_status': status
        }

        if status == "error" and errors:
            result['error'] = errors.get('error')
            result['error_details'] = errors.get('error_details')
            message += ": " + result['error']
            if result['error_details']:
                message += ". Details: " + result['error_details']

        if message:
            self.ctx.log(message)
        else:
            self.ctx.log('Search status is %s' % status)

        
        return result

    @error_handler
    @authenticated
    @with_dataset
    def history(self, dataset):
        name = self.ctx.config.get('experiment/name', None)
        if name is None:
            raise AugerException('Please specify Experiment name...')
        for exp_run in iter(Experiment(self.ctx, dataset, name).history()):
            self.ctx.log("run id: {}, start time: {}, status: {}".format(
                exp_run.get('id'),
                exp_run.get('model_settings').get('start_time'),
                exp_run.get('status')))
        return {'history': Experiment(self.ctx, dataset, name).history()}
