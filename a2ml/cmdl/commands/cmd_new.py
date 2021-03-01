import os
import sys
import errno
import click

from a2ml.api.utils.context import PROVIDERS
from a2ml.cmdl.utils.template import Template
from a2ml.api.utils.context import pass_context
from a2ml.api.auger.impl.cloud.dataset import AugerDataSetApi
from a2ml.api.utils import fsclient


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
        if not self.ctx.config.path:
            project_path = os.path.join(os.getcwd(), self.project_name)
        else:
            project_path = self.ctx.config.path

        if not fsclient.is_s3_path(project_path):
            project_path = os.path.abspath(project_path)

        if fsclient.is_folder_exists(project_path):
            raise Exception(
                'Can\'t create \'%s\'. Folder already exists.' % \
                    self.project_name)

        fsclient.create_folder(project_path)    
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
            config.set('providers',
                PROVIDERS if self.providers == 'all' else self.providers, config_name='config')
            config.set('name', self.project_name, config_name='config')
            config.set('target', self.target, config_name='config')
            config.set('source', self.source, config_name='config')
            config.set('model_type', self.model_type, config_name='config')
            config.write('config')

            if self.model_type != 'classification':
                self.ctx.config.set('experiment/metric', 'r2_score', config_name='azure')
                self.ctx.config.write('azure')
                self.ctx.config.set('experiment/metric', 'r2', config_name='auger')
                self.ctx.config.write('auger')

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.ctx.log('%s', str(e))
            #sys.exit(1)


@click.command('new', short_help='Create new A2ML project.')
@click.argument('project', required=True, type=click.STRING)
@click.option('--providers', '-p', default='auger',
    type=click.Choice(['all','auger','google','azure','external']),
    help='Model Provider.')
@click.option('--source', '-s',  default='', type=click.STRING,
    help='Data source local file or remote url.')
@click.option('--model-type', '-mt', default='classification',
    type=click.Choice(['classification','regression']),
    help='Model Type.')
@click.option('--target', '-t',  default='', type=click.STRING,
    help='Target column name in data source.')
@pass_context
def cmdl(ctx, project, providers, source, model_type, target):
    """Create new A2ML project."""
    ctx.setup_logger(format='')
    NewCmd(ctx, project, providers,
        target, source, model_type).create_project()
