from a2ml.api.utils.crud_runner import CRUDRunner
from a2ml.api.utils.error_handler import ErrorHandler

class A2MLExperiment(metaclass=ErrorHandler):

    def __init__(self, ctx, provider):
        super(A2MLExperiment, self).__init__()
        self.ctx = ctx
        self.runner = CRUDRunner(ctx, provider, 'experiment')

    def list(self):
        self.runner.execute('list')

    def start(self):
        self.runner.execute('start')

    def stop(self):
        self.runner.execute('stop')

    def leaderboard(self, run_id):
        self.runner.execute('leaderboard', run_id)

    def history(self):
        self.runner.execute('history')
