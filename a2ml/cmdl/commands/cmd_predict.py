import click

from a2ml.api.auger.predict import AugerPredict
from a2ml.cmdl.utils.context import pass_context
from a2ml.cmdl.utils.provider_operations import ProviderOperations

class PredictCmd(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def predict(self, filename, deployed_model_id, threshold):
        operations = {
            'auger': AugerPredict(self.ctx.copy('auger')).predict
        }
        ProviderOperations(self.ctx).execute(
            self.ctx.get_providers(), operations, filename=filename,
            deployed_model_id=deployed_model_id, threshold=threshold)


@click.command('predict', short_help='Predict with deployed model.')
@click.argument('filename', required=True, type=click.STRING)
@click.option('--threshold', '-t', default=None, type=float,
    help='Threshold.')
@click.option('--deployed-model-id', '-m',  type=click.STRING,
    help='Deployed model id.')
@pass_context
def cmdl(ctx, filename, deployed_model_id, threshold):
    """Predict with deployed model."""
    ctx.setup_logger(format='')
    PredictCmd(ctx).predict(filename, deployed_model_id, threshold)
