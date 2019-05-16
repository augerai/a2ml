import click

from a2ml.cmdl.cmdl import pass_context
from a2ml.api import gc_a2ml
from a2ml.api import az_a2ml
import yaml
import os

class TrainCmd(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def train(self):
        print("Directory: {}".format(os.getcwd()))
        # TODO: @vlad: how do I get the path where the current project is!
        config = yaml.safe_load(open("ex1/config.yaml"))
        providers=config['providers'].split(',')
        for provider in providers: 
            if provider == "GC":
                model = gc_a2ml.GCModel(config['name'],config['project'],config['region'])
                model.train(config['dataset_id'],config['target'],config['exclude'].split(','),config['budget'],config['metric'])
            elif provider == "AZ":
                # name,project_id,compute_region,compute_name
                model = az_a2ml.AZModel(config['name'],config['project'],config['azure_region'],config['azure_compute_name'])
                model.train(config['azure_source'],config['target'],config['exclude'].split(','),config['budget'],config['azure_metric'])


@click.command('train', short_help='Train the model.')
@pass_context
def cmdl(ctx):
    """Train the model."""
    ctx.setup_logger(format='')
    TrainCmd(ctx).train()
