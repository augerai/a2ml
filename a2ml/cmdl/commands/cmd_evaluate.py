import click
from a2ml.api.a2ml import A2ML
from a2ml.api.utils.context import pass_context


@click.command('evaluate', short_help='Evaluate models after training.')
@click.argument('run-id', required=False, type=click.STRING)
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def cmdl(ctx, run_id, provider):
    """Evaluate models after training."""
    ctx.setup_logger(format='')
    A2ML(ctx, provider).evaluate(run_id)
