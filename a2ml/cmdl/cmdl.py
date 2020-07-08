import sys
import click
from a2ml.api.utils.context import CONTEXT_SETTINGS
from a2ml.api.utils.context import pass_context

COMMANDS = [
  'auth',
  'new',
  'import',
  'train',
  'evaluate',
  'deploy',
  'predict',
  'project',
  'dataset',
  'experiment',
  'model',
  'server',
  'worker'
]


class A2mlCli(click.MultiCommand):
    def list_commands(self, ctx):
        return COMMANDS

    def get_command(self, ctx, name):
        try:
            if sys.version_info[0] == 2:
                name = name.encode('ascii', 'replace')
            mod = __import__('a2ml.cmdl.commands.cmd_' + name,
                             None, None, ['cli'])
        except ImportError:
            import traceback
            traceback.print_exc()
            return
        return mod.cmdl


@click.command(cls=A2mlCli, context_settings=CONTEXT_SETTINGS)
@click.version_option()
@pass_context
def cmdl(ctx):
    """A2ML command line interface."""
