import click
from a2ml.api.a2ml_experiment import A2MLExperiment
from a2ml.api.utils.context import pass_context


@click.group('experiment', short_help='Experiment management')
@pass_context
def cmdl(ctx):
    """Experiment management"""
    ctx.setup_logger(format='')


@click.command(short_help='List Experiments for selected DataSet')
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def list_cmd(ctx, provider):
    """List Experiments for selected DataSet"""
    A2MLExperiment(ctx, provider).list()


@click.command(short_help='Start Experiment')
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def start(ctx, provider):
    """Start Experiment.
       If Experiment is not selected, new Experiment will be created.
    """
    A2MLExperiment(ctx, provider).start()


@click.command(short_help='Stop Experiment')
@click.argument('run-id', required=False, type=click.STRING)
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def stop(ctx, provider, run_id):
    """Stop Experiment"""
    A2MLExperiment(ctx, provider).stop(run_id)


@click.command(short_help='Show Experiment leaderboard')
@click.argument('run-id', required=False, type=click.STRING)
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def leaderboard(ctx, provider, run_id):
    """Show Experiment leaderboard for specified run id.
       If run id is not provided, latest experiment run
       leaderboard will be shown.
    """
    A2MLExperiment(ctx, provider).leaderboard(run_id)

@click.command(short_help='Show Experiment history')
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def history(ctx, provider):
    """Show Experiment history"""
    A2MLExperiment(ctx, provider).history()


@pass_context
def add_commands(ctx):
    cmdl.add_command(list_cmd, name='list')
    cmdl.add_command(start)
    cmdl.add_command(stop)
    cmdl.add_command(leaderboard)
    cmdl.add_command(history)


add_commands()
