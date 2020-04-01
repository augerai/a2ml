from celery import Celery

import redis
import time

app = Celery('hello', broker='redis://localhost:6379/0')

redis_connection = redis.StrictRedis(host='localhost', port=6379)

def log(*args):
    print(*args)

@app.task(name='tasks.process_transaction')
def process_transaction(id):
    log(f"Process transaction {id}")
    redis_connection.publish(id, f"Process transaction {id}")

    time.sleep(5)
    log(f"Continue processing transaction {id}")
    redis_connection.publish(id, f"Continue processing transaction {id}")

    time.sleep(5)
    log(f"One step more processing transaction {id}")
    redis_connection.publish(id, f"One step more processing transaction {id}")

    time.sleep(5)
    log(f"Processing transaction is done {id}")
    redis_connection.publish(id, f"Processing transaction is done {id}")
    redis_connection.publish(id, 'done')
    return 'hello world'
