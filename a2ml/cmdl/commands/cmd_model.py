import click
from a2ml.api.a2ml_model import A2MLModel
from a2ml.api.utils.context import pass_context


@click.group('model', short_help='Model management')
@pass_context
def cmdl(ctx):
    """Model management"""
    ctx.setup_logger(format='')

@click.command('deploy', short_help='Deploy trained model.')
@click.argument('model-id', required=True, type=click.STRING)
@click.option('--locally', is_flag=True, default=False,
    help='Download and deploy trained model locally.')
@click.option('--provider', '-p', type=click.STRING, required=False,
    help='Cloud AutoML Provider.')
@pass_context
def deploy(ctx, provider, model_id, locally):
    """Deploy trained model."""
    A2MLModel(ctx, provider).deploy(model_id, locally)

@click.command('predict', short_help='Predict with deployed model.')
@click.argument('filename', required=True, type=click.STRING)
@click.option('--threshold', '-t', default=None, type=float,
    help='Threshold.')
@click.option('--model-id', '-m', type=click.STRING, required=True,
    help='Deployed model id.')
@click.option('--locally', is_flag=True, default=False,
    help='Predict locally using Docker image to run model.')
@click.option('--provider', '-p', type=click.STRING, required=False,
    help='Cloud AutoML Provider.')
@pass_context
def predict(ctx, provider, filename, model_id, threshold, locally):
    """Predict with deployed model."""
    A2MLModel(ctx, provider).predict(filename, model_id, threshold, locally)

@click.command('actual', short_help='Send actual values for deployed model. Needed for review and monitoring.')
@click.argument('filename', required=True, type=click.STRING)
@click.option('--model-id', '-m', type=click.STRING, required=True,
    help='Deployed model id.')
@click.option('--provider', '-p', type=click.STRING, required=False,
help='Cloud AutoML Provider.')
@pass_context
def actual(ctx, provider, filename, model_id):
    """Predict with deployed model."""
    A2MLModel(ctx, provider).actual(filename, model_id)


@pass_context
def add_commands(ctx):
    cmdl.add_command(deploy)
    cmdl.add_command(predict)
    cmdl.add_command(actual)


add_commands()
