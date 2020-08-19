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
@click.option('--no-review', is_flag=True, default=False,
    help='Do not support model review based on actual data.')
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def deploy(ctx, provider, model_id, locally, no_review):
    """Deploy trained model."""
    A2MLModel(ctx, provider).deploy(model_id, locally, not no_review)

@click.command('predict', short_help='Predict with deployed model.')
@click.argument('filename', required=True, type=click.STRING)
@click.option('--threshold', '-t', default=None, type=float,
    help='Threshold.')
@click.option('--model-id', '-m', type=click.STRING, required=True,
    help='Deployed model id.')
@click.option('--locally', is_flag=True, default=False,
    help='Predict locally using Docker image to run model.')
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@click.option('--output', '-o', type=click.STRING, required=False,
    help='Output csv file path.')
@pass_context
def predict(ctx, provider, filename, model_id, threshold, locally, output):
    """Predict with deployed model."""
    A2MLModel(ctx, provider).predict(filename, model_id, threshold=threshold, locally=locally, output=output)

@click.command('actuals', short_help='Send actual values for deployed model. Needed for review and monitoring.')
@click.argument('filename', required=True, type=click.STRING)
@click.option('--model-id', '-m', type=click.STRING, required=True,
    help='Deployed model id.')
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
help='Cloud AutoML Provider.')
@click.option('--locally', is_flag=True, default=False,
    help='Process actuals locally.')
@pass_context
def actuals(ctx, provider, filename, model_id, locally):
    """Predict with deployed model."""
    A2MLModel(ctx, provider).actuals(model_id, filename=filename, locally=locally)

@click.command('review', short_help='Review the performance of deployed model.')
@click.option('--model-id', '-m', type=click.STRING, required=True,
    help='Deployed model id.')
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def review(ctx, provider, model_id, output):
    """Predict with deployed model."""
    A2MLModel(ctx, provider).review(model_id)

@click.command('undeploy', short_help='Undeploy trained model.')
@click.argument('model-id', required=True, type=click.STRING)
@click.option('--locally', is_flag=True, default=False,
    help='Undeploy trained model locally.')
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def undeploy(ctx, provider, model_id, locally):
    """Undeploy trained model."""
    A2MLModel(ctx, provider).undeploy(model_id, locally)

@click.command('delete_actuals', short_help='Delete files with actuals and predcitions locally or from specified provider(s).')
@click.option('--model-id', '-m', type=click.STRING, required=True,
    help='Deployed model id.')
@click.option('--with-predictions', is_flag=True, default=False,
    help='Remove predictions.')
@click.option('--begin-date', '-b', type=click.STRING, required=False,
    help='Date to begin delete operations.')
@click.option('--end-date', '-e', type=click.STRING, required=False,
    help='Date to end delete operations.')
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
help='Cloud AutoML Provider.')
@click.option('--locally', is_flag=True, default=False,
    help='Process actuals locally.')
@pass_context
def delete_actuals(ctx, model_id, with_predictions, begin_date, end_date, provider, locally):
    """Predict with deployed model."""
    A2MLModel(ctx, provider).delete_actuals(model_id, 
        with_predictions=with_predictions, begin_date=begin_date, end_date=end_date, locally=locally)

@pass_context
def add_commands(ctx):
    cmdl.add_command(deploy)
    cmdl.add_command(predict)
    cmdl.add_command(actuals)
    cmdl.add_command(review)
    cmdl.add_command(undeploy)
    cmdl.add_command(delete_actuals)

add_commands()
