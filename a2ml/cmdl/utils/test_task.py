import time

class TestTask(object):
    """TestTask"""
    def __init__(self, ctx):
        super(TestTask, self).__init__()
        self.ctx = ctx

    def iterate(self):
        self.ctx.log('Starting test task...')
        for x in range(5):
            self.ctx.log('Iteration %s' % x)
            time.sleep(2)
            self.ctx.log('Iteration %s done' % x)
