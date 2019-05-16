import click

from a2ml.cmdl.cmdl import pass_context
from a2ml.api.auger.import_data import AugerImport
from a2ml.api import gc_a2ml
# import yaml

class ImportCmd(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def import_data(self):
        provider = self.ctx.config.get('provider', None)
        import_provider = {
            'auger': AugerImport(self.ctx).import_data
        }
        runner = import_provider.get(provider, lambda:
            self.ctx.log('Provider is not specified.'
                         ' Please create experiment using "new" command'
                         ' and run import command from experiment folder...'))
        runner()

@click.command('import', short_help='Import data for training.')
@pass_context
def cmdl(ctx):
    """Import data for training."""
    ctx.setup_logger(format='')
    ImportCmd(ctx).import_data()
