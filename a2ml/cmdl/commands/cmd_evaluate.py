import click
from a2ml.api.a2ml import A2ML
from a2ml.api.utils.context import pass_context


@click.command('evaluate', short_help='Evaluate models after training.')
@click.option('--provider', '-p', type=click.STRING, required=False,
    help='Cloud AutoML Provider.')
@pass_context
def cmdl(ctx, provider):
    """Evaluate models after training."""
    ctx.setup_logger(format='')
    A2ML(ctx, provider).evaluate()
