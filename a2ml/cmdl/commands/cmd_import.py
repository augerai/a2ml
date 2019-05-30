import click

from a2ml.cmdl.utils.test_task import TestTask
from a2ml.cmdl.utils.context import pass_context
from a2ml.api.auger.import_data import AugerImport
from a2ml.cmdl.utils.provider_operations import ProviderOperations
from a2ml.api import gc_a2ml
# import yaml

class ImportCmd(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def import_data(self):
        operations = {
            'auger': AugerImport(self.ctx.copy('auger')).import_data,
            'google': TestTask(self.ctx.copy('google')).iterate,
            'azure': TestTask(self.ctx.copy('azure')).iterate
        }
        ProviderOperations(self.ctx).execute(
            self.ctx.get_providers(), operations)

@click.command('import', short_help='Import data for training.')
@pass_context
def cmdl(ctx):
    """Import data for training."""
    ctx.setup_logger(format='')
    ImportCmd(ctx).import_data()
