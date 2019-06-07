class GoogleA2ML(object):
    """Google A2ML implementation."""

    def __init__(self, ctx):
        super(GoogleA2ML, self).__init__()
        self.ctx = ctx

    def import_data(self):
        self.ctx.log('Google Import Data')

    def train(self):
        self.ctx.log('Google Train')

    def evaluate(self):
        self.ctx.log('Google Evaluate')

    def deploy(self, model_id, locally=False):
        self.ctx.log('Google Deploy')

    def predict(self, filename, model_id, threshold=None, locally=False):
        self.ctx.log('Google Predict')

    def review(self):
        self.ctx.log('Google Review')
