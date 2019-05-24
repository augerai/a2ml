import click

from a2ml.api.auger.auth import AugerAuth
from a2ml.cmdl.utils.context import pass_context

class AuthCmd(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def login(self,username, password, url):
        AugerAuth(self.ctx).login(username, password, url)

    def logout(self):
        AugerAuth(self.ctx).logout()

    def whoami(self):
        AugerAuth(self.ctx).whoami()

@click.group('auth', short_help='Authenticate with AutoML provider.')
@pass_context
def cmdl(ctx):
    """Authenticate with AutoML provider."""
    ctx.setup_logger(format='')

@click.command(short_help='Login to Auger.')
@click.option('--username', '-u', default=None, prompt='username',
    type=click.STRING, help='Auger username.')
@click.password_option('--password', '-p', prompt='password',
    confirmation_prompt=False, help='Auger password.')
@click.option('--url', default=None, type=click.STRING, help='Auger API endpoint.')
@pass_context
def login(ctx, username, password, url):
    """Login to Auger."""
    AuthCmd(ctx).login(username, password, url)

@click.command(short_help='Logout from Auger.')
@pass_context
def logout(ctx):
    """Logout from Auger."""
    AuthCmd(ctx).logout()

@click.command(short_help='Display the current logged in user.')
@pass_context
def whoami(ctx):
    """Display the current logged in user."""
    ctx.setup_logger(format='')
    AuthCmd(ctx).whoami()


@pass_context
def add_commands(ctx):
    cmdl.add_command(login)
    cmdl.add_command(logout)
    cmdl.add_command(whoami)

add_commands()
