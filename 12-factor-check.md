# 12-Factor Check — `app.py`

Fill in the **Status** (✅ / ⚠️ / ❌) and one line of **Why** for each factor.
Then compare with your Day 1 notes.

| # | Factor | Status | Why |
|---|---|---|---|
| 1 | Codebase | ✅ | One Git repo (`cloud-native-30`), one `app.py` — ready to deploy to many environments from the same code. |
| 2 | Dependencies | ✅ | Every package pinned with exact version in `requirements.txt` (e.g. `fastapi==0.115.6`), no system-wide installs assumed. |
| 3 | Config | ✅ | All settings read via `os.getenv(...)` with safe defaults — `DATABASE_URL`, `REDIS_URL`, `APP_VERSION`, `CELERY_EAGER`, `LOG_LEVEL`. No secrets in code. |
| 4 | Backing services | ✅ | Postgres and Redis attached by URL — swapping local Redis → AWS ElastiCache = change `REDIS_URL` env, no code change. |
| 5 | Build, release, run | ⚠️ | Currently running from source (`uvicorn app:app`). No image build stage yet — will add on **Day 2 (Dockerfile)**. |
| 6 | Processes (stateless) | ⚠️ | API + worker are stateless (state in Postgres/Redis), but local default uses SQLite `./local.db` on disk — fine for dev, not for K8s. Prod uses Postgres → fully stateless. |
| 7 | Port binding | ✅ | Uvicorn serves HTTP directly on port 8000. No external Apache/Nginx needed inside the container. |
| 8 | Concurrency | ✅ | Two separate process types — API (uvicorn) and worker (celery). Each can scale out independently (Day 10 KEDA). |
| 9 | Disposability | ⚠️ | `task_acks_late=True` lets a dead worker's job retry elsewhere. `lifespan` disposes DB engine on shutdown. But no explicit SIGTERM handler for in-flight HTTP requests (uvicorn handles it by default). |
| 10 | Dev/prod parity | ❌ | Dev uses SQLite + `CELERY_EAGER=true` (no Redis/worker). Prod uses Postgres + real Celery worker. Big divergence — fix with Docker Compose (Day 7+). |
| 11 | Logs | ✅ | `logging.basicConfig(...)` writes to stdout. No log files on disk. Kubernetes/Loki will collect the stream (Day 23). |
| 12 | Admin processes | ❌ | `Base.metadata.create_all(engine)` runs schema creation **inside the app on startup** (line 134). With 3 replicas, 3 pods try to create the schema at once. Should be a separate one-off job — **fix on Day 9 (Alembic migrations as K8s Job)**. |

## What to fix later
| Factor | Fix | Day |
|---|---|---|
| 5 Build, release, run | Build a Docker image; keep release config in env, not baked in | Day 2 |
| 6 Processes | Switch default from SQLite to Postgres (via Docker) so no local disk state | Day 7 |
| 9 Disposability | Add `preStop` hook in K8s + verify graceful shutdown under load | Day 14 |
| 10 Dev/prod parity | Run same Postgres + Redis locally via `docker compose` / kind | Day 7 |
| 12 Admin processes | Move `create_all` out of the app; run Alembic migrations as a Kubernetes Job | Day 9 |
