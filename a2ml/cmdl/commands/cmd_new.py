import os
import errno
import click

from a2ml.cmdl.cmdl import pass_context
from a2ml.cmdl.utils.template import Template

class NewCmd(object):

    def __init__(self, ctx, app_name):
        self.ctx = ctx
        self.app_name = app_name

    def mk_app_folder(self):
        app_path = os.path.abspath(os.path.join(os.getcwd(), self.app_name))
        try:
            os.makedirs(app_path)
        except OSError as e:
            if e.errno == errno.EEXIST:
                raise Exception('Can\'t create \'%s\'. Folder already exists.' % self.app_name)
            raise
        self.ctx.log('Created application folder %s', self.app_name)
        return app_path

    def create_app(self):
        try:
            app_path = self.mk_app_folder()
            Template.copy(app_path)
            self.ctx.log('To run application, please do: cd %s && a2ml train' % self.app_name)

        except Exception as e:
            self.ctx.log('%s', str(e))


@click.command('new', short_help='Create new A2ML application.')
@click.argument('app-name', required=True, type=click.STRING)
@pass_context
def cmdl(ctx, app_name):
    """Create new A2ML application."""
    ctx.setup_logger(format='')
    NewCmd(ctx, app_name).create_app()
