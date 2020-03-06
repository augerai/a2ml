from a2ml.api.utils.crud_runner import CRUDRunner
from a2ml.api.utils.error_handler import ErrorHandler

class A2MLExperiment(metaclass=ErrorHandler):

    def __init__(self, ctx, provider):
        super(A2MLExperiment, self).__init__()
        self.ctx = ctx
        self.runner = CRUDRunner(ctx, provider, 'experiment')

    def list(self):
        return self.runner.execute('list')

    def start(self):
        return self.runner.execute('start')

    def stop(self):
        return self.runner.execute('stop')

    def leaderboard(self, run_id):
        return self.runner.execute('leaderboard', run_id)

    def history(self):
        return self.runner.execute('history')
