# Development

## Deps

```
pip install ".[server]"
```

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
a2ml server -r true
```

Run Celery worker:
```
a2ml worker
```

Add these options in your `config.yaml`:
```
use_server: true
server_endpoint: http://localhost:8000
```

Use CLI as usual
```
a2ml project list
```
