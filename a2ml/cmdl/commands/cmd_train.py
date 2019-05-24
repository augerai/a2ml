import click

from a2ml.cmdl.utils.test_task import TestTask
from a2ml.cmdl.utils.context import pass_context
from a2ml.api.auger.train import AugerTrain
from a2ml.cmdl.utils.provider_operations import ProviderOperations
from a2ml.api import gc_a2ml

class TrainCmd(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def train(self):
        providers = self.ctx.config['config'].get('providers', [])
        operations = {
            'auger': AugerTrain(self.ctx.copy('auger')).train,
            'google': TestTask(self.ctx.copy('google')).iterate,
            'azure': TestTask(self.ctx.copy('azure')).iterate
        }
        ProviderOperations(self.ctx).execute(providers, operations)

@click.command('train', short_help='Train the model.')
@pass_context
def cmdl(ctx):
    """Train the model."""
    ctx.setup_logger(format='')
    TrainCmd(ctx).train()
