import click
from a2ml.api.a2ml import A2ML
from a2ml.api.utils.context import pass_context


@click.command('deploy', short_help='Deploy trained model.')
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@click.argument('model-id', required=True, type=click.STRING)
@click.option('--locally', is_flag=True, default=False,
    help='Download and deploy trained model locally.')
@click.option('--no-review', is_flag=True, default=False,
    help='Do not support model review based on actual data.')
@pass_context
def cmdl(ctx, provider, model_id, locally, no_review):
    """Deploy trained model."""
    ctx.setup_logger(format='')
    A2ML(ctx, provider).deploy(model_id, locally, not no_review)
