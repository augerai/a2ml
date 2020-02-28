import os
import sys
import errno
import click

from a2ml.api.auger.config import AugerConfig
from a2ml.api.utils.context import PROVIDERS
from a2ml.cmdl.utils.template import Template
from a2ml.api.utils.context import pass_context
from auger.api.cloud.data_set import AugerDataSetApi
from a2ml.api.auger.credentials import Credentials


class NewCmd(object):

    def __init__(self, ctx, project_name,
        providers, target, source, model_type):
        self.ctx = ctx
        self.project_name = project_name
        self.providers = providers
        self.target = target
        self.source = source
        self.model_type = model_type

    def mk_project_folder(self):
        project_path = os.path.abspath(
            os.path.join(os.getcwd(), self.project_name))
        try:
            os.makedirs(project_path)
        except OSError as e:
            if e.errno == errno.EEXIST:
                raise Exception(
                    'Can\'t create \'%s\'. Folder already exists.' % \
                        self.project_name)
            raise
        self.ctx.log('Created project folder %s', self.project_name)
        return project_path

    def create_project(self):
        try:
            if self.source:
                self.source = AugerDataSetApi.verify(self.source)[0]

            project_path = self.mk_project_folder()
            Template.copy_config_files(project_path, ['config'] + PROVIDERS)
            self.ctx.log('To build your model, please do:'
                ' cd %s && a2ml import && a2ml train' % \
                self.project_name)

            config = self.ctx.config
            config.load(project_path, True)
            config.set('config', 'providers',
                PROVIDERS if self.providers == 'all' else self.providers)
            config.set('config', 'name', self.project_name)
            config.set('config', 'target', self.target)
            config.set('config', 'source', self.source)
            config.set('config', 'model_type', self.model_type)
            config.write('config')

            if self.model_type != 'classification':
                self.ctx.config.set('azure', 'experiment/metric', 'spearman_correlation')
                self.ctx.config.write('azure')
                self.ctx.config.set('auger', 'experiment/metric', 'r2')
                self.ctx.config.write('auger')

        except Exception as e:
            # import traceback
            # traceback.print_exc()
            self.ctx.log('%s', str(e))
            sys.exit(1)


@click.command('new', short_help='Create new A2ML project.')
@click.argument('project', required=True, type=click.STRING)
@click.option('--providers', '-p', default='auger',
    type=click.Choice(['all','auger','google','azure']),
    help='Model Provider.')
@click.option('--source', '-s',  default='', type=click.STRING,
    help='Data source local file or remote url.')
@click.option('--model-type', '-mt', default='classification',
    type=click.Choice(['classification','regression','timeseries']),
    help='Model Type.')
@click.option('--target', '-t',  default='', type=click.STRING,
    help='Target column name in data source.')
@pass_context
def cmdl(ctx, project, providers, source, model_type, target):
    """Create new A2ML project."""
    ctx.setup_logger(format='')
    NewCmd(ctx, project, providers,
        target, source, model_type).create_project()
