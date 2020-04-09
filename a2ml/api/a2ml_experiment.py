from a2ml.api.base_a2ml import BaseA2ML
from a2ml.api.utils.show_result import show_result

class A2MLExperiment(BaseA2ML):

    def __init__(self, ctx, provider):
        super(A2MLExperiment, self).__init__()
        self.ctx = ctx
        self.runner = self.build_runner(ctx, provider, 'experiment')

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
