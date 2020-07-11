import click
from a2ml.api.a2ml import A2ML
from a2ml.api.utils.context import pass_context


@click.command('train', short_help='Train the model.')
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def cmdl(ctx, provider):
    """Train the model."""
    ctx.setup_logger(format='')
    A2ML(ctx, provider).train()
