import click
from a2ml.api.a2ml_project import A2MLProject
from a2ml.api.utils.context import pass_context

@click.group('project', short_help='Projects management')
@pass_context
def cmdl(ctx):
    """Project(s) management"""
    ctx.setup_logger(format='')

@click.command(short_help='List Projects')
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def list_cmd(ctx, provider):
    """List Projects"""
    A2MLProject(ctx, provider).list()

@click.command(short_help='Create Project')
@click.argument('name', required=False, type=click.STRING)
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def create(ctx, provider, name):
    """Create Project"""
    A2MLProject(ctx, provider).create(name)

@click.command(short_help='Delete Project')
@click.argument('name', required=False, type=click.STRING)
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def delete(ctx, provider, name):
    """Delete Project"""
    A2MLProject(ctx, provider).delete(name)


@click.command(short_help='Select Project')
@click.argument('name', required=True, type=click.STRING)
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def select(ctx, provider, name):
    """Select Project.
       Name will be set in provider.yaml/project
    """
    A2MLProject(ctx, provider).select(name)


@pass_context
def add_commands(ctx):
    cmdl.add_command(list_cmd, name='list')
    cmdl.add_command(create)
    cmdl.add_command(delete)
    cmdl.add_command(select)


add_commands()
