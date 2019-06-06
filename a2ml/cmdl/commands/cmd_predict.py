import click

from a2ml.api.auger.predict import AugerPredict
from a2ml.cmdl.utils.context import pass_context
from a2ml.cmdl.utils.provider_operations import ProviderOperations
from a2ml.api.google.predict import GooglePredict
class PredictCmd(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def predict(self, filename, model_id, threshold, locally):
        operations = {
            'auger': AugerPredict(self.ctx.copy('auger')).predict,
            'google': GooglePredict(self.ctx.copy('google')).predict
        }
        ProviderOperations(self.ctx).execute(
            self.ctx.get_providers(), operations,
            filename=filename, model_id=model_id,
            threshold=threshold, locally=locally)


@click.command('predict', short_help='Predict with deployed model.')
@click.argument('filename', required=True, type=click.STRING)
@click.option('--threshold', '-t', default=None, type=float,
    help='Threshold.')
@click.option('--model-id', '-m', type=click.STRING, required=True,
    help='Deployed model id.')
@click.option('--locally', is_flag=True, default=False,
    help='Predict locally using Docker image to run model.')
@pass_context
def cmdl(ctx, filename, model_id, threshold, locally):
    """Predict with deployed model."""
    ctx.setup_logger(format='')
    PredictCmd(ctx).predict(filename, model_id, threshold, locally)
