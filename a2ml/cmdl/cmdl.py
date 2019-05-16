import os
import sys
import click
import logging

from a2ml.cmdl.utils.config_yaml import ConfigYaml

log = logging.getLogger("a2ml")

CONTEXT_SETTINGS = dict(auto_envvar_prefix='A2ML')
PROVIDERS = ['auger', 'google', 'azure', 'h2o']
PROVIDERS_META = '|'.join(PROVIDERS)

class Context(object):

    def __init__(self):
        self.config = self.load_config()

    def log(self, msg, *args, **kwargs):
        log.info(msg, *args, **kwargs)

    def load_config(self):
        config = ConfigYaml()
        if os.path.isfile('config.yaml'):
            config.load_from_file('config.yaml')
        return config

    @staticmethod
    def setup_logger(format='%(asctime)s %(name)s | %(message)s'):
        logging.basicConfig(
            stream=sys.stdout,
            datefmt='%H:%M:%S',
            format=format,
            level=logging.INFO)


pass_context = click.make_pass_decorator(Context, ensure=True)


class A2mlCli(click.MultiCommand):
    cmd_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), 'commands'))

    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(A2mlCli.cmd_folder):
            if filename.endswith('.py') and \
               filename.startswith('cmd_'):
                rv.append(filename[4:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        try:
            if sys.version_info[0] == 2:
                name = name.encode('ascii', 'replace')
            mod = __import__('a2ml.cmdl.commands.cmd_' + name,
                             None, None, ['cli'])
        except ImportError as e:
            print(name)
            print(str(e))
            return
        return mod.cmdl


@click.command(cls=A2mlCli, context_settings=CONTEXT_SETTINGS)
@pass_context
def cmdl(ctx):
    """A2ML command line interface."""
