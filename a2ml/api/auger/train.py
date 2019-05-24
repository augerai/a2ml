from a2ml.api.auger.base import AugerBase


class AugerTrain(AugerBase):
    """Train you Model on Auger."""
    def __init__(self, ctx):
        super(AugerTrain, self).__init__(ctx)
        self.ctx = ctx

    def train(self):
        self.ctx.log('In progress...')
