import click

from a2ml.cmdl.cmdl import pass_context

class EvaluateCmd(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def evaluate(self):
        pass


@click.command('evaluate', short_help='Evaluate models after training.')
@pass_context
def cmdl(ctx):
    """Evaluate models after training."""
    ctx.setup_logger(format='')
    EvaluateCmd(ctx).evaluate()
