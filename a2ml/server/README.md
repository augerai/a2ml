# Development

## Deps

Uses these packages:
```
asyncio
asyncio-redis
fastapi
gevent
jsonpickle
redis
uvicorn
```

## Test

Run dev server:
```
cd a2ml/server
uvicorn server:app --reload
```

Run Celery worker:
```
cd a2ml/tasks_queue
celery -A celery_app worker --loglevel=info --pool=gevent -c 100
```

Add these options in your config.yaml:
```
use_server: true
server_endpoint: http://localhost:8000
```

Use CLI as usual
```
a2ml project list
```
