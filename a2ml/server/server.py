from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.encoders import jsonable_encoder

import asyncio
import uuid
import websockets
import sys

from a2ml.tasks_queue.tasks_api import new_project_task, list_projects_task, delete_project_task, select_project_task, \
    new_dataset_task, list_datasets_task, delete_dataset_task, select_dataset_task, \
    list_experiments_task, leaderboard_experiment_task, history_experiment_task, \
    start_experiment_task, stop_experiment_task, \
    actuals_model_task, actuals_task, deploy_model_task, predict_model_task, \
    deploy_task, evaluate_task, import_data_task, predict_task, train_task, review_task


from a2ml.server.config import Config
from a2ml.server.notification import AsyncReceiver

app = FastAPI()
config = Config()

API_SCHEMA = {
    '/api/v1/datasets': {
        'get': list_datasets_task,
        'post': new_dataset_task,
        'delete': delete_dataset_task,
    },
    '/api/v1/datasets/select': {
        'patch': select_dataset_task,
    },
    '/api/v1/deploy': {
        'patch': deploy_task,
    },
    '/api/v1/evaluate': {
        'patch': evaluate_task,
    },
    '/api/v1/experiments': {
        'get': list_experiments_task,
    },
    '/api/v1/experiments/history': {
        'get': history_experiment_task,
    },
    '/api/v1/experiments/leaderboard': {
        'get': leaderboard_experiment_task,
    },
    '/api/v1/experiments/start': {
        'patch': start_experiment_task,
    },
    '/api/v1/experiments/stop': {
        'patch': stop_experiment_task,
    },
    '/api/v1/import_data': {
        'patch': import_data_task,
    },
    '/api/v1/models/actuals': {
        'post': actuals_model_task,
    },
    '/api/v1/actuals': {
        'post': actuals_task,
    },    
    '/api/v1/models/deploy': {
        'patch': deploy_model_task,
    },
    '/api/v1/models/predict': {
        'post': predict_model_task,
    },
    '/api/v1/predict': {
        'post': predict_task,
    },
    '/api/v1/projects': {
        'get': list_projects_task,
        'post': new_project_task,
        'delete': delete_project_task,
    },
    '/api/v1/projects/select': {
        'patch': select_project_task,
    },
    '/api/v1/review': {
        'patch': review_task,
    },
    '/api/v1/train': {
        'patch': train_task,
    },
}

@app.get('/hello')
async def say_hello():
    await asyncio.sleep(1)
    return {'Hello': 'World'}

@app.post('/api/v1/upload_credentials')
def upload_credentials():
    # TODO: replace with Vault generated credentials

    # To use locally replace endpoint with localhost because CLI client can't access interfaces inside docker componse
    if config.s3_endpoint_url.startswith('http://minio:9000'):
        endpoint_url = 'http://localhost:9000'
    else:
        endpoint_url = config.s3_endpoint_url

    return __render_json_response({
        'bucket': config.upload_bucket,
        'endpoint_url': endpoint_url,
        'access_key': config.aws_access_key_id,
        'secret_key': config.aws_secret_access_key,
        'session_token': None
    })

def define_endpoints(schema):
    for path in schema.keys():
        endpoints = schema[path]
        for http_verb in endpoints.keys():
            task = endpoints[http_verb]
            define_endpoint(http_verb, path, task)

def define_endpoint(http_verb, path, task):
    decorator_method = getattr(app, http_verb)

    @decorator_method(path)
    async def handler(request: Request):
        return await __run_task(task, request)

    setattr(sys.modules[__name__], task.__name__.replace('_task', ''), handler)

define_endpoints(API_SCHEMA)

def log(*args):
    print(*args)

async def __run_task(task, request):
    request_id = __generate_request_id()
    params = await __get_body_and_query_params(request)
    params['_request_id'] = request_id
    task.delay(params)
    return __render_request_response(request_id)

async def __get_body_and_query_params(request):
    params = dict(request.query_params)
    if len(await request.body()) > 0:
        params.update(await request.json())

    return params

def __render_request_response(request_id):
    return __render_json_response({ 'request_id': request_id })

def __render_json_response(data):
    res = {
        'meta': { 'status': 200 },
        'data': data,
    }

    content = jsonable_encoder(res)
    return JSONResponse(content=content)

def __generate_request_id():
    return str(uuid.uuid4())

@app.websocket("/ws")
# id - id of request
async def websocket_endpoint(websocket: WebSocket, id: str = None, last_msg_id: str = '0'):
    try:
        if id:
            await websocket.accept()
            await websocket.send_json({"type": "start", 'request_id': id}, mode="text")

            try:
                notificator = AsyncReceiver(id, last_msg_id)
                try:
                    while True:
                        try:
                            # Periodically iterrupt waiting of message from subscription
                            # to check is websocket is still alive or not
                            reply = await asyncio.wait_for(notificator.get_message(), timeout=5.0)
                            if reply:
                                log("Broadcast: ", repr(reply))
                                await websocket.send_text(reply)
                            else:
                                await websocket.send_json({"type": "ping"}, mode="text")
                        except asyncio.TimeoutError:
                            await websocket.send_json({"type": "ping"}, mode="text")
                except (websockets.exceptions.ConnectionClosedOK, websockets.exceptions.ConnectionClosedError) as e:
                    log(f"WebSocket {id} disconnected: {str(e)}")
            finally:
                await notificator.close()
    finally:
        log('WebSocket stopped')
        await websocket.close()
