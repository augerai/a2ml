import click
from a2ml.api.a2ml_dataset import A2MLDataset
from a2ml.api.utils.context import pass_context


@click.group('dataset', short_help='Dataset(s) management')
@pass_context
def cmdl(ctx):
    """Dataset(s) management"""
    ctx.setup_logger(format='')


@click.command(short_help='List Data Sets on Provider Cloud')
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def list_cmd(ctx, provider):
    """List Provider remote datasets"""
    A2MLDataset(ctx, provider).list()


@click.command(short_help='Create Dataset on Provider Cloud')
@click.argument('source', required=False, type=click.STRING)
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def create(ctx, provider, source):
    """Create data set on the Provider Cloud.
       If source is not specified, config.yaml/source
       will be used instead.
    """
    A2MLDataset(ctx, provider).create(source)


@click.command(short_help='Delete Dataset on Provider Cloud')
@click.argument('name', required=False, type=click.STRING)
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def delete(ctx, provider, name):
    """Delete Dataset on the Provider Cloud
       If name is not specified, config.yaml/dataset
       will be used instead.
    """
    A2MLDataset(ctx, provider).delete(name)


@click.command(short_help='Select Dataset')
@click.argument('name', required=False, type=click.STRING)
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def select(ctx, provider, name):
    """Select data set.
       Name will be set in config.yaml/dataset
    """
    A2MLDataset(ctx, provider).select(name)


@pass_context
def add_commands(ctx):
    cmdl.add_command(list_cmd, name='list')
    cmdl.add_command(create)
    cmdl.add_command(delete)
    cmdl.add_command(select)


add_commands()
