import click
import os

from a2ml.api.utils.context import pass_context

@click.command('worker', short_help='Run Celery worker')
@click.option('--pool', '-p', type=click.STRING, required=False, default='prefork',
    show_default=True, help='host interface to bind server')
@click.option('--concurrency', '-c', type=click.INT, required=False, default=4,
    show_default=True, help='port to bind server')
@pass_context
def cmdl(ctx, pool, concurrency):
    cmd_line = f'celery -A a2ml.tasks_queue.celery_app worker --loglevel=info --pool={pool} -c {concurrency}'
    os.system(cmd_line)
