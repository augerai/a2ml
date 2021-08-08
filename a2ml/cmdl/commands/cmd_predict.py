import click
from a2ml.api.a2ml import A2ML
from a2ml.api.utils.context import pass_context


@click.command('predict', short_help='Predict with deployed model.')
@click.argument('model-id', required=True, type=click.STRING)
@click.argument('filename', required=True, type=click.STRING)
@click.option('--threshold', '-t', default=None, type=float,
    help='Threshold.')
@click.option('--score', '-s', is_flag=True, default=False,
    help='Calculate scores for predicted results.')
@click.option('--score_true_path', type=click.STRING, required=False,
    help='Path to true values to calculate scores. If missed, target from filename used for true values.')
@click.option('--locally', '-l', is_flag=True, default=False,
    help='Predict locally using auger.ai.predict package.')
@click.option('--docker', is_flag=True, default=False,
    help='Predict locally using Docker image to run model.')
@click.option('--output', '-o', type=click.STRING, required=False,
    help='Output csv file path.')
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def cmdl(ctx, provider, filename, model_id, threshold, locally, docker, output):
    """Predict with deployed model."""
    ctx.setup_logger(format='')
    if docker:
        locally = "docker"
    A2ML(ctx, provider).predict( model_id, filename=filename, 
        threshold=threshold, score=score, score_true_data=score_true_path,
        locally=locally, output=output)
