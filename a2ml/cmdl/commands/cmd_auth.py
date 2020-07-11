import click

from a2ml.api.a2ml_credentials import A2MLCredentials
from a2ml.api.utils.context import pass_context

class AuthCmd(object):

    def __init__(self, ctx, provider='auger'):
        self.ctx = ctx
        self.provider = provider

    def login(self,username, password, organization, url):
        A2MLCredentials(self.ctx, self.provider).login(username, password, organization, url)

    def logout(self):
        A2MLCredentials(self.ctx, self.provider).logout()

    def whoami(self):
        A2MLCredentials(self.ctx, self.provider).whoami()

def prompt_login(ctx, param, provider):
    system = ctx.params.get('system','production')
    if provider == 'auger':
        username = ctx.params.get('username')
        if not username:
            username = click.prompt('username', default=None)

        organization = ctx.params.get('organization')
        if not organization:
            organization = click.prompt('organization', default=None)

        password = ctx.params.get('password')
        if not password:
            password = click.prompt('password', default=None, confirmation_prompt=False, hide_input=True)

        return {'username':username, 'organization':organization, 'password':password, 'system':system, 'name':provider}
    return {'username':None, 'organization':None, 'password':None, 'system':system, 'name':provider}

@click.group('auth', short_help='Authenticate with AutoML provider.')
@pass_context
def cmdl(ctx):
    """Authenticate with AutoML provider."""
    ctx.setup_logger(format='')

@click.command(short_help='Login to a provider.')
@click.option('--provider', '-p', default='auger', help='Provider name.', callback=prompt_login, show_default=True)
@click.option('--username', '-u', default=None, type=click.STRING, help='Provider username.', is_eager=True)
@click.option('--organization', '-o', default=None, type=click.STRING, help='Provider organization.', is_eager=True)
@click.option('--password', '-w', confirmation_prompt=False, default=None, help='Provider password.', is_eager=True, hide_input=True)
@click.option('--system', '-s', default='production',
    type=click.Choice(['production','staging']), help='Auger Provider endpoint.', show_default=True)
@pass_context
def login(ctx, username, password, organization, system, provider):
    """Login to a provider."""
    urls = {
        'production': 'https://app.auger.ai',
        'staging': 'https://app-staging.auger.ai'}
    AuthCmd(ctx, provider['name']).login(provider['username'], provider['password'], provider['organization'], urls[provider['system']])

@click.command(short_help='Logout from a provider.')
@click.option('--provider', '-p', default='auger', type=click.Choice(['auger','azure']), help='Provider name.', show_default=True)
@pass_context
def logout(ctx, provider):
    """Logout from a provider."""
    AuthCmd(ctx, provider).logout()

@click.command(short_help='Display the current logged in user for a provider.')
@click.option('--provider', '-p', default='auger', type=click.Choice(['auger','azure']), help='Provider name.', show_default=True)
@pass_context
def whoami(ctx, provider):
    """Display the current logged in user."""
    ctx.setup_logger(format='')
    AuthCmd(ctx, provider).whoami()


@pass_context
def add_commands(ctx):
    cmdl.add_command(login)
    cmdl.add_command(logout)
    cmdl.add_command(whoami)

add_commands()
