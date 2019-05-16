import os
import errno
import click

from a2ml.cmdl.cmdl import pass_context, PROVIDERS, PROVIDERS_META
from a2ml.cmdl.utils.template import Template

class NewCmd(object):

    def __init__(self, ctx, experiment_name, provider):
        self.ctx = ctx
        self.experiment_name = experiment_name
        self.provider = provider

    def mk_experiment_folder(self):
        experiment_path = os.path.abspath(os.path.join(os.getcwd(), self.experiment_name))
        try:
            os.makedirs(experiment_path)
        except OSError as e:
            if e.errno == errno.EEXIST:
                raise Exception('Can\'t create \'%s\'. Folder already exists.' % self.experiment_name)
            raise
        self.ctx.log('Created experiment folder %s', self.experiment_name)
        return experiment_path

    def create_experiment(self):
        try:
            experiment_path = self.mk_experiment_folder()
            Template.copy(experiment_path, self.provider)
            self.ctx.log('To run experiment, please do: cd %s && a2ml train' % self.experiment_name)

        except Exception as e:
            self.ctx.log('%s', str(e))


@click.command('new', short_help='Create new A2ML experiment.')
@click.argument('experiment-name', required=True, type=click.STRING)
@click.option('--provider', '-p', default='auger', metavar='',
              type=click.Choice(PROVIDERS),
              help='[%s]\nAutoML provider to use in this experiment.' % PROVIDERS_META)
@pass_context
def cmdl(ctx, experiment_name, provider):
    """Create new A2ML experiment."""
    ctx.setup_logger(format='')
    NewCmd(ctx, experiment_name, provider).create_experiment()
