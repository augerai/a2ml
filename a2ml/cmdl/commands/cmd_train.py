import click

from a2ml.cmdl.cmdl import pass_context

class TrainCmd(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def train(self):
        pass


@click.command('train', short_help='Train the model.')
@pass_context
def cmdl(ctx):
    """Train the model."""
    ctx.setup_logger(format='')
    TrainCmd(ctx).train()
