import click

from a2ml.cmdl.utils.context import pass_context

class DeployCmd(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def deploy(self):
        pass


@click.command('deploy', short_help='Deploy trained model.')
@pass_context
def cmdl(ctx):
    """Deploy trained model."""
    ctx.setup_logger(format='')
    DeployCmd(ctx).deploy()
