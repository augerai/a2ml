import asyncio
import json
import requests
import websockets

def log(*args):
    print(*args)

async def run_and_wait_transaction():
    response = requests.get("http://localhost:8000/start_transaction")

    if response.status_code == 200:
        id = response.text

        async with websockets.connect("ws://localhost:8000/ws?id=" + id) as websocket:
            while True:
                data = await websocket.recv()
                data = json.loads(data)
                log(data)

                if 'message' in data and data['message'] == 'done':
                    log('Transaction done')
                    break
    else:
        log(f"Error in start_transaction {response.status_code} {response.text}")

asyncio.get_event_loop().run_until_complete(run_and_wait_transaction())
