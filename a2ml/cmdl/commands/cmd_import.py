import click

from a2ml.cmdl.cmdl import pass_context
from a2ml.api.auger.import_data import AugerImport
from a2ml.api import gc_a2ml
# import yaml

class ImportCmd(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def import_data(self):
        providers = self.ctx.config['config'].get('providers', [])
        self.ctx.log('Importing to %s' % ', '.join(providers))
        import_providers = {
            'auger': AugerImport(self.ctx).import_data
        }
        for provider in providers:
            importer = import_providers.get(provider, lambda:
                self.ctx.log(
                    'Importer for %s is not implemented yet...'
                    % provider.capitalize()))
            importer()

@click.command('import', short_help='Import data for training.')
@pass_context
def cmdl(ctx):
    """Import data for training."""
    ctx.setup_logger(format='')
    ImportCmd(ctx).import_data()
