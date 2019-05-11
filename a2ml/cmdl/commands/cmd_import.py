import click

from a2ml.cmdl.cmdl import pass_context
from a2ml.cmdl.cmdl import pass_context
from a2ml.api import gc_a2ml
import yaml

class ImportCmd(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def import_data(self):
        config = yaml.safe_load(open("config.yaml"))
        if config['provider'] == "GC":
            print("Project: {}".format(config['project']))
            model = gc_a2ml.GCModel(config['name'],config['project'],config['region'])
            model.import_data(config['source'])
            config['dataset_id']=model.dataset_id
            config['operation_id']=model.operation_id
        with open('config.yaml', 'w') as yaml_file:
            yaml.dump(config, yaml_file, default_flow_style=False)

@click.command('import', short_help='Import data for training.')
@pass_context
def cmdl(ctx):
    """Import data for training."""
    ctx.setup_logger(format='')
    ImportCmd(ctx).import_data()
