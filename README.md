# Cloud-Native 30

A FastAPI + PostgreSQL + Redis + Celery app, taken from local to Kubernetes on AWS in 30 days.

## Run locally (Windows PowerShell)

```powershell
# 1. Create and activate a virtual environment (first time only)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install packages
pip install -r requirements.txt

# 3. Quick run: SQLite + tasks run inline (no worker or Redis needed)
$env:CELERY_EAGER="true"
uvicorn app:app --reload
```

Open http://localhost:8000/docs and try every endpoint.
Without Redis, `/readyz` returns 503. That is expected.

## Run with a real worker (needs Redis)

```powershell
# Terminal 1: Redis in Docker
docker run -d --name redis -p 6379:6379 redis:7

# Terminal 2: API
uvicorn app:app --reload

# Terminal 3: Celery worker (--pool=solo is needed on Windows)
celery -A app.celery_app worker --loglevel=info --pool=solo
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Version + pod name |
| GET | `/healthz` | Liveness probe |
| GET | `/readyz` | Readiness probe (checks DB + Redis) |
| POST | `/notes` | Create a note, send it to Celery |
| GET | `/notes` | List notes |
| GET | `/notes/{id}` | Read one note (Redis cache) |
