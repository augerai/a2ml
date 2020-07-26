import os

class Config:
    def __init__(self):
        self.debug = os.environ.get('DEBUG', 'false').lower() == 'true'
        self.broker_url = os.environ.get('BROKER_URL', 'amqp://localhost/vhost')
        self.task_result_queue = os.environ.get('TASK_RESULT_QUEUE', 'task_result')
