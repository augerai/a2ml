import click

from a2ml.cmdl.utils.context import pass_context

class PredictCmd(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def predict(self):
        pass


@click.command('predict', short_help='Predict with deployed model.')
@pass_context
def cmdl(ctx):
    """Predict with deployed model."""
    ctx.setup_logger(format='')
    PredictCmd(ctx).predict()
