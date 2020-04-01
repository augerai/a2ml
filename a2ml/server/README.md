# Development

## Deps

Install these packages:
```
fastapi
uvicorn
redis
asyncio
asyncio-redis
```

## Test

Run dev server:
```
cd a2ml/server
uvicorn main:app --reload
```

Run Celery worker:
```
celery -A tasks worker --loglevel=info
```


Run one on more clients
```
python client.py
```

Go to http://localhost:8000/ and click `Start transaction`
