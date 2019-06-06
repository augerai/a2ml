import click
from a2ml.cmdl.utils.context import pass_context
from a2ml.api.auger.evaluate import AugerEvaluate
from a2ml.cmdl.utils.provider_operations import ProviderOperations
from a2ml.api.google.evaluate import GoogleEvaluate
class EvaluateCmd(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def evaluate(self):
        operations = {
            'auger': AugerEvaluate(self.ctx.copy('auger')).evaluate,
            'google': GoogleEvaluate(self.ctx.copy('google')).evaluate
        }
        ProviderOperations(self.ctx).execute(self.ctx.get_providers(), operations)

@click.command('evaluate', short_help='Evaluate models after training.')
@pass_context
def cmdl(ctx):
    """Evaluate models after training."""
    ctx.setup_logger(format='')
    EvaluateCmd(ctx).evaluate()
