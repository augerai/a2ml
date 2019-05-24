import os
import sys
import click
from a2ml.cmdl.utils.context import Context
from a2ml.cmdl.utils.context import CONTEXT_SETTINGS
from a2ml.cmdl.utils.context import pass_context


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
            return
        return mod.cmdl


@click.command(cls=A2mlCli, context_settings=CONTEXT_SETTINGS)
@pass_context
def cmdl(ctx):
    """A2ML command line interface."""
