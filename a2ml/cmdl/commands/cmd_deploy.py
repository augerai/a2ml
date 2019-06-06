import click

from a2ml.api.auger.deploy import AugerDeploy
from a2ml.cmdl.utils.context import pass_context
from a2ml.cmdl.utils.provider_operations import ProviderOperations
from a2ml.api.google.deploy import GoogleDeploy

class DeployCmd(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def deploy(self, model_id, locally):
        operations = {
            'auger': AugerDeploy(self.ctx.copy('auger')).deploy
        }
        ProviderOperations(self.ctx).execute(
            self.ctx.get_providers(), operations,
            model_id=model_id, locally=locally)


@click.command('deploy', short_help='Deploy trained model.')
@click.argument('model-id', required=True, type=click.STRING)
@click.option('--locally', is_flag=True, default=False,
    help='Download and deploy trained model locally.')
@pass_context
def cmdl(ctx, model_id, locally):
    """Deploy trained model."""
    ctx.setup_logger(format='')
    DeployCmd(ctx).deploy(model_id, locally)
