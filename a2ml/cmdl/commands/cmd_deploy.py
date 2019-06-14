import click
from a2ml.api.a2ml import A2ML
from a2ml.api.utils.context import pass_context

class DeployCmd(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def deploy(self, model_id, locally):
        operations = {
            'auger': AugerDeploy(self.ctx.copy('auger')).deploy,
            'google': GoogleDeploy(self.ctx.copy('google')).deploy
        }
        ProviderOperations(self.ctx).execute(
            self.ctx.get_providers(), operations,
            model_id=model_id, locally=locally)

@click.command('deploy', short_help='Deploy trained model.')
@click.argument('model-id', required=False, type=click.STRING)
@click.option('--locally', is_flag=True, default=False,
    help='Download and deploy trained model locally.')
@pass_context
def cmdl(ctx, model_id, locally):
    """Deploy trained model."""
    ctx.setup_logger(format='')
    A2ML(ctx).deploy(model_id, locally)
