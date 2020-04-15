# Disable warnings
def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn

from celery import Celery
from kombu import Exchange, Queue
import os
import logging


celeryApp = Celery('a2ml.tasks_queue',
             include=[
             'a2ml.tasks_queue.tasks_api'])

celeryApp.conf.enable_utc = True
celeryApp.conf.broker_url = os.environ.get(
    "BROKER_URL",
    "redis://%s:%s/0" % (
        os.environ.get('REDIS_HOST', 'localhost'),
        os.environ.get('REDIS_PORT', '6379')
    )
)

# TODO: for AMQP there better to use "rpc://"
# see https://docs.celeryproject.org/en/4.0/whatsnew-4.0.html#features-removed-for-lack-of-funding
# now leave it optional and not RPC by default
if celeryApp.conf.broker_url.lower().startswith('amqp'):
    if os.environ.get('RESULT_RPC', 'false').lower() == 'true':
        celeryApp.conf.result_backend = "rpc://"
    else:
        celeryApp.conf.result_backend = "amqp://"
else:
    celeryApp.conf.result_backend = celeryApp.conf.broker_url

# Next settings for result queues should be absolutely the same as declared in concumer
# else amqp.exceptions.PreconditionFailed: Queue.declare: (406) PRECONDITION_FAILED
# will be raised
celeryApp.conf.result_expires = int(os.environ.get('CELERY_RESULT_EXPIRES_SEC', 86400)) # 24 hours
celeryApp.conf.result_persistent = True

celeryApp.conf.task_acks_late = False
celeryApp.conf.task_send_sent_event = True

from kombu.utils import json as _json
from a2ml.api.utils.json_utils import convert_simple_numpy_type

class NumpyKombuJSONEncoder(_json.JSONEncoder):
    """ Special json encoder for numpy types """
    def default(self, obj):
        res = convert_simple_numpy_type(obj)
        if res is not None:
            return res

        return super(NumpyKombuJSONEncoder, self).default(obj)

# Encoder function
def my_dumps(obj):
    return _json.dumps(obj, cls=NumpyKombuJSONEncoder)

# Register your new serializer methods into kombu
from kombu.serialization import register

register('myjson', my_dumps, _json.loads,
    content_type='application/json',
    content_encoding='utf-8')

# Tell celery to use your new serializer:
#celeryApp.conf.accept_content = ['myjson']
celeryApp.conf.task_serializer = 'myjson'
celeryApp.conf.result_serializer = 'myjson'

# try monkey patch startup timeout since we take longer than 4.0 seconds to startup
from celery.concurrency import asynpool
asynpool.PROC_ALIVE_TIMEOUT = 60.0

