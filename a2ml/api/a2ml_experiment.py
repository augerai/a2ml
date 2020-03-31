from a2ml.api.utils.crud_runner import CRUDRunner
from a2ml.api.utils.show_result import show_result

class A2MLExperiment(object):

    def __init__(self, ctx, provider):
        super(A2MLExperiment, self).__init__()
        self.ctx = ctx
        self.runner = CRUDRunner(ctx, provider, 'experiment')

    @show_result
    def list(self):
        return self.runner.execute('list')

    @show_result
    def start(self):
        return self.runner.execute('start')

    @show_result
    def stop(self):
        return self.runner.execute('stop')

    @show_result
    def leaderboard(self, run_id):
        return self.runner.execute('leaderboard', run_id)

    @show_result
    def history(self):
        return self.runner.execute('history')
