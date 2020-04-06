import os

class Config:
    def __init__(self):
        self.celery_broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
        self.debug = os.environ.get('DEBUG', 'false').lower() == 'true'
        self.notificator_redis_host = os.environ.get('NOTIFICATOR_REDIS_HOST', 'localhost')
        self.notificator_redis_port = int(os.environ.get('NOTIFICATOR_REDIS_PORT', 6379))
