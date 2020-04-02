from celery import Celery

import redis
import time
import requests

from a2ml.server.config import Config
from a2ml.server.notification import SyncSender

config = Config()

app = Celery('hello', broker=config.celery_broker_url)

# with prefork Celery mode sender can be shared in global var
# Note: for CPU-bound use prefork mode, for IO-bound gevent mode
# https://www.distributedpython.com/2018/10/26/celery-execution-pool/
sender = SyncSender()

def log(*args):
    print(*args)

@app.task(name='tasks.process_transaction')
def process_transaction(id):
    log(f"Process transaction {id}")
    sender.publish(id, f"Process transaction {id}")

    time.sleep(5)
    log(f"Continue processing transaction {id}")
    sender.publish(id, f"Continue processing transaction {id}")

    time.sleep(5)
    log(f"One step more processing transaction {id}")
    sender.publish(id, f"One step more processing transaction {id}")

    time.sleep(5)
    log(f"Processing transaction is done {id}")
    sender.publish(id, f"Processing transaction is done {id}")
    sender.publish(id, 'done')
    return 'hello world'

@app.task(name='tasks.http_call_task')
def http_call_task(url):
    response = requests.get(url)
    return [response.status_code, len(response.text)]
