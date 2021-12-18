import click
from a2ml.api.a2ml import A2ML
from a2ml.api.utils.context import pass_context

@click.command('import', short_help='Import data for training.')
@click.option('--source', '-s', type=click.STRING, required=False,
    help='Source file to import.If skipped, then import source from config.yml.')
@click.option('--description', '-d', type=click.STRING, required=False,
    help='Description of dataset.')
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def cmdl(ctx, source, description, provider):
    """Import data for training."""
    ctx.setup_logger(format='')
    A2ML(ctx, provider).import_data(source, description=description)
