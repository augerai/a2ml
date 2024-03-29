import click
from a2ml.api.a2ml_model import A2MLModel
from a2ml.api.utils.context import pass_context
from a2ml.api.utils.formatter import print_table

@click.group('model', short_help='Model management')
@pass_context
def cmdl(ctx):
    """Model management"""
    ctx.setup_logger(format='')

@click.command('deploy', short_help='Deploy trained model.')
@click.argument('model-id', required=False, type=click.STRING)
@click.option('--locally', is_flag=True, default=False,
    help='Download and deploy trained model locally.')
@click.option('--review', is_flag=True, default=False,
    help='Do not support model review based on actual data.')
@click.option('--provider', '-p', type=click.Choice(['auger','azure','external']), required=False,
    help='Cloud AutoML Provider.')
@click.option('--name', '-n', required=False, type=click.STRING, 
    help='Model friendly name.Used as name for Review Endpoint')
@click.option('--algorithm', '-a', required=False, type=click.STRING, 
    help='Monitored model(external provider) algorithm name.')
@click.option('--score', '-s', required=False, type=float, 
    help='Monitored model(external provider) score.')
@click.option('--data-path', '-d', type=click.STRING, required=False,
    help='Data path to fit model when deploy. Return new deployed model-id')
@pass_context
def deploy(ctx, provider, model_id, locally, review, name, algorithm, score, data_path):
    """Deploy trained model."""
    A2MLModel(ctx, provider).deploy(model_id, locally=locally, review=review, 
        name=name, algorithm=algorithm, score=score, data_path=data_path)

@click.command('predict', short_help='Predict with deployed model.')
@click.argument('model-id', required=True, type=click.STRING)
@click.argument('filename', required=True, type=click.STRING)
@click.option('--threshold', '-t', default=None, type=float,
    help='Threshold.')
@click.option('--score', '-s', is_flag=True, default=False,
    help='Calculate scores for predicted results.')
@click.option('--score_true_path', type=click.STRING, required=False,
    help='Path to true values to calculate scores. If missed, target from filename used for true values.')
@click.option('--locally', '-l', is_flag=True, default=False,
    help='Predict locally using auger.ai.predict package.')
@click.option('--docker', is_flag=True, default=False,
    help='Predict locally using Docker image to run model.')
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@click.option('--output', '-o', type=click.STRING, required=False,
    help='Output csv file path.')
@pass_context
def predict(ctx, provider, filename, model_id, threshold, locally, docker, output):
    """Predict with deployed model."""
    if docker:
        locally = "docker"

    A2MLModel(ctx, provider).predict(model_id, filename=filename, 
        threshold=threshold, score=score, score_true_data=score_true_path,
        locally=locally, output=output)

@click.command('actuals', short_help='Send actual values for deployed model. Needed for review and monitoring.')
@click.argument('model-id', required=True, type=click.STRING)
@click.argument('filename', required=True, type=click.STRING)
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
help='Cloud AutoML Provider.')
@click.option('--locally', is_flag=True, default=False,
    help='Process actuals locally.')
@pass_context
def actuals(ctx, provider, filename, model_id, locally):
    """Predict with deployed model."""
    A2MLModel(ctx, provider).actuals(model_id, filename=filename, locally=locally)

@click.command('review_alert', short_help='Update Review Alert parameters from config.')
@click.argument('model-id', required=True, type=click.STRING)
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@click.option('--name', '-n', required=False, type=click.STRING, 
    help='Model friendly name.Used as name for Review Endpoint')
@pass_context
def review_alert(ctx, provider, model_id, name):
    """Predict with deployed model."""
    A2MLModel(ctx, provider).review_alert(model_id, name=name)

@click.command('review', short_help='Review information about deployed model.')
@click.argument('model-id', required=True, type=click.STRING)
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def review(ctx, provider, model_id):
    """Review information about deployed model."""
    result = A2MLModel(ctx, provider).review(model_id)
    ctx.log('Review information for %s: %s' % (model_id, result))

@click.command('undeploy', short_help='Undeploy trained model.')
@click.argument('model-id', required=True, type=click.STRING)
@click.option('--locally', is_flag=True, default=False,
    help='Undeploy trained model locally.')
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def undeploy(ctx, provider, model_id, locally):
    """Undeploy trained model."""
    A2MLModel(ctx, provider).undeploy(model_id, locally)

@click.command('delete_actuals', short_help='Delete files with actuals and predcitions locally or from specified provider(s).')
@click.argument('model-id', required=True, type=click.STRING)
@click.option('--with-predictions', is_flag=True, default=False,
    help='Remove predictions.')
@click.option('--begin-date', '-b', type=click.STRING, required=False,
    help='Date to begin delete operations.')
@click.option('--end-date', '-e', type=click.STRING, required=False,
    help='Date to end delete operations.')
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
help='Cloud AutoML Provider.')
@click.option('--locally', is_flag=True, default=False,
    help='Process actuals locally.')
@pass_context
def delete_actuals(ctx, model_id, with_predictions, begin_date, end_date, provider, locally):
    A2MLModel(ctx, provider).delete_actuals(model_id, 
        with_predictions=with_predictions, begin_date=begin_date, end_date=end_date, locally=locally)

@click.command('get_info', short_help='Get information about model.')
@click.argument('model-id', required=True, type=click.STRING)
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
help='Cloud AutoML Provider.')
@click.option('--locally', is_flag=True, default=False,
    help='Process actuals locally.')
@pass_context
def get_info(ctx, model_id, provider, locally):
    result = A2MLModel(ctx, provider).get_info(model_id, locally=locally)

    ctx.log('Model information for %s: %s' % (model_id, result))

@click.command(short_help='List Deployed models')
@click.option('--endpoints', is_flag=True, default=False,
    help='List endpoints.')
@click.option('--provider', '-p', type=click.Choice(['auger','azure']), required=False,
    help='Cloud AutoML Provider.')
@pass_context
def list_cmd(ctx, endpoints, provider):
    """List Projects"""
    res = A2MLModel(ctx, provider).list(endpoints=endpoints)

    models = []
    res = res.get('data', {}).get('models', [])
    res.sort(key=lambda t: t['created_at'], reverse=True)
    for item in res[:10]:
        if endpoints:
            models.append({
                'ID': item.get('id'),
                'Name': item.get('name'),
            })            
        else:        
            trial = item.get('trial', {})
            models.append({
                'ID': item.get('id'),
                'Algorithm': trial.get('hyperparameter', {}).get('algorithm_name'),
                'Score': trial.get('score_name') + ':' + '{0:.3f}'.format(trial.get('score_value')),
                'dataset': item.get('datasource_manifest_name')
            })
    print_table(ctx.log, models)

@pass_context
def add_commands(ctx):
    cmdl.add_command(list_cmd, name='list')
    cmdl.add_command(deploy)
    cmdl.add_command(predict)
    cmdl.add_command(actuals)
    cmdl.add_command(review_alert)
    cmdl.add_command(review)
    cmdl.add_command(undeploy)
    cmdl.add_command(delete_actuals)
    cmdl.add_command(get_info)

add_commands()
