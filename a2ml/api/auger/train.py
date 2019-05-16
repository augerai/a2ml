

class AugerTrain(object):
    """Train you Model on Auger."""
    def __init__(self, ctx):
        super(Train, self).__init__()
        self.ctx = ctx

    def train(self):
        self.ctx.log('In progress...')
