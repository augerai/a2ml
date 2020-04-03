from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.encoders import jsonable_encoder

import asyncio
import uuid
import websockets

from a2ml.tasks_queue.tasks_api import new_project_task, list_projects_task
from a2ml.server.notification import AsyncReceiver

app = FastAPI()

def log(*args):
    print(*args)

@app.get("/hello")
async def read_root():
    await asyncio.sleep(1)
    return {"Hello": "World"}

@app.get("/start_transaction", response_class=PlainTextResponse)
def start_transaction():
    id = _generate_request_id()
    process_transaction.delay(id)
    return id

@app.get("/http_call")
def http_call(url: str = None):
    http_call_task.delay(url)
    return 'ok'

# @app.post("/api/v1/projects")
# def create_project():
#     request_id = _generate_request_id()
#     new_project_task.delay(request_id)
#     return _render_response(request_id)

@app.get("/api/v1/projects")
async def list_projects(request: Request):
    request_id = _generate_request_id()
    params = await _get_body_and_query_params(request)
    params['_request_id'] = request_id
    list_projects_task.delay(params)
    return _render_response(request_id)

async def _get_body_and_query_params(request):
    params = dict(request.query_params)
    if len(await request.body()) > 0:
        params.update(await request.json())

    return params

def _render_response(request_id):
    res = {
        'meta': { 'status': 200 },
        'data': { 'request_id': request_id },
    }

    content = jsonable_encoder(res)
    return JSONResponse(content=content)

def _generate_request_id():
    return str(uuid.uuid4())

@app.websocket("/ws")
# id - id of request
async def websocket_endpoint(websocket: WebSocket, id: str = None):
    try:
        if id:
            await websocket.accept()
            await websocket.send_json({"type": "start", 'request_id': id}, mode="text")

            with AsyncReceiver(id) as notificator:
                try:
                    while True:
                        try:
                            # Periodically iterrupt waiting of message from subscription
                            # to check is websocket is still alive or not
                            reply = await asyncio.wait_for(notificator.get_message(), timeout=5.0)
                            log("Received: ", repr(reply))
                            await websocket.send_text(reply)
                        except asyncio.TimeoutError:
                            await websocket.send_json({"type": "ping"}, mode="text")
                except (websockets.exceptions.ConnectionClosedOK, websockets.exceptions.ConnectionClosedError) as e:
                    log(f"WebSocket {id} disconnected: {str(e)}")
    finally:
        log('WebSocket stopped')
        await websocket.close()
