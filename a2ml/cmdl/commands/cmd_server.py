import click

from a2ml.api.utils.context import pass_context

@click.command('server', short_help='Run server')
@click.option('--host', '-h', type=click.STRING, required=False, default='0.0.0.0',
    show_default=True, help='host interface to bind server')
@click.option('--port', '-p', type=click.INT, required=False, default=8000,
    show_default=True, help='port to bind server')
@click.option('--reload', '-r', type=click.BOOL, required=False, default=False,
    show_default=True, help='enable autoreload')
@click.option('--workers', '-w', type=click.INT, required=False, default=1,
    show_default=True, help='workers count')
@pass_context
def cmdl(ctx, host, port, reload, workers):
    import uvicorn

    uvicorn.run(
        "a2ml.server.server:app",
        host=host, port=port, log_level="info", reload=reload, workers=workers
    )
