import click

from a2ml.cmdl.utils.context import pass_context

class ReviewCmd(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def review(self):
        pass


@click.command('review', short_help='Review specified model info.')
@pass_context
def cmdl(ctx):
    """Review specified model info."""
    ctx.setup_logger(format='')
    ReviewCmd(ctx).review()
