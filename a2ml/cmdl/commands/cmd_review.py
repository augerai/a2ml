import click
from a2ml.api.a2ml import A2ML
from a2ml.api.utils.context import pass_context


@click.command('review', short_help='Review specified model info.')
@pass_context
def cmdl(ctx):
    """Review specified model info."""
    ctx.setup_logger(format='')
    A2ML(ctx).review()
