import click

from a2ml.cmdl.utils.context import pass_context
from a2ml.api.auger.evaluate import AugerEvaluate
from a2ml.cmdl.utils.provider_operations import ProviderOperations

class EvaluateCmd(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def evaluate(self):
        providers = self.ctx.config['config'].get('providers', [])
        operations = {
            'auger': AugerEvaluate(self.ctx.copy('auger')).evaluate
        }
        ProviderOperations(self.ctx).execute(providers, operations)

@click.command('evaluate', short_help='Evaluate models after training.')
@pass_context
def cmdl(ctx):
    """Evaluate models after training."""
    ctx.setup_logger(format='')
    EvaluateCmd(ctx).evaluate()
