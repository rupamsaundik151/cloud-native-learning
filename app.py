"""
Cloud-Native 30 — demo app
FastAPI API + PostgreSQL + Redis + Celery worker, in one file.

Run the API:     uvicorn app:app --host 0.0.0.0 --port 8000
Run the worker:  celery -A app.celery_app worker --loglevel=info

All config comes from environment variables (12-factor, Day 1).
"""
import logging
import os
import socket
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import redis
from celery import Celery
from fastapi import Depends, FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Integer, String, Text, create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

# ---------------------------------------------------------------------------
# Config (12-factor: everything from env, safe local defaults)
# ---------------------------------------------------------------------------
APP_VERSION = os.getenv("APP_VERSION", "v1")  # change per rollout (Day 4, Day 20)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_EAGER = os.getenv("CELERY_EAGER", "false").lower() == "true"  # run tasks inline (no worker) for local tests
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 12-factor: logs go to stdout, Kubernetes collects them (Day 23 → Loki)
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("cn30")

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | processed
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)  # worker pod name
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Redis (cache) + Celery (background jobs)
# ---------------------------------------------------------------------------
redis_client = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=2, decode_responses=True)

celery_app = Celery("cn30", broker=CELERY_BROKER_URL)
celery_app.conf.update(
    task_always_eager=CELERY_EAGER,
    task_acks_late=True,  # if a worker pod dies mid-task, another one retries it (Day 28)
    worker_prefetch_multiplier=1,
)


@celery_app.task(name="process_note", bind=True, max_retries=3)
def process_note(self, note_id: int) -> dict:
    """Pretend heavy work: count words, mark note processed."""
    time.sleep(1)  # simulate slow work → useful for KEDA autoscaling demo (Day 10)
    with SessionLocal() as db:
        note = db.get(Note, note_id)
        if note is None:
            log.warning("note %s not found", note_id)
            return {"note_id": note_id, "status": "missing"}
        note.word_count = len(note.body.split())
        note.status = "processed"
        note.processed_by = socket.gethostname()  # shows which pod did the work
        db.commit()
    try:
        redis_client.delete(f"note:{note_id}")  # invalidate cache
    except redis.RedisError:
        pass
    log.info("processed note %s", note_id)
    return {"note_id": note_id, "status": "processed"}


# ---------------------------------------------------------------------------
# API schemas
# ---------------------------------------------------------------------------
class NoteIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1)


class NoteOut(BaseModel):
    id: int
    title: str
    body: str
    status: str
    word_count: int | None
    processed_by: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(_: FastAPI):
    # Fine for learning. From Day 9, run Alembic migrations as a K8s Job instead.
    Base.metadata.create_all(engine)
    log.info("app started version=%s pod=%s", APP_VERSION, socket.gethostname())
    yield
    engine.dispose()
    log.info("app stopped")


app = FastAPI(title="Cloud-Native 30", version=APP_VERSION, lifespan=lifespan)


@app.get("/")
def root():
    # The pod name helps you see load balancing across replicas (Day 4–5)
    return {"app": "cn30", "version": APP_VERSION, "pod": socket.gethostname()}


@app.get("/healthz")
def liveness():
    """Liveness probe: is the process alive? Never check dependencies here."""
    return {"status": "ok"}


@app.get("/readyz")
def readiness(response: Response):
    """Readiness probe: can this pod serve traffic? Checks Postgres and Redis."""
    checks = {}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["database"] = f"error: {exc.__class__.__name__}"
    try:
        redis_client.ping()
        checks["redis"] = "ok"
    except redis.RedisError as exc:
        checks["redis"] = f"error: {exc.__class__.__name__}"

    ready = all(v == "ok" for v in checks.values())
    response.status_code = status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return {"ready": ready, "checks": checks}


@app.post("/notes", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(payload: NoteIn, db: Session = Depends(get_db)):
    note = Note(title=payload.title, body=payload.body)
    db.add(note)
    db.commit()
    db.refresh(note)
    process_note.delay(note.id)  # hand off to Celery worker
    if CELERY_EAGER:
        db.refresh(note)
    return note


@app.get("/notes", response_model=list[NoteOut])
def list_notes(limit: int = 20, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 100))
    return db.scalars(select(Note).order_by(Note.id.desc()).limit(limit)).all()


@app.get("/notes/{note_id}", response_model=NoteOut)
def get_note(note_id: int, db: Session = Depends(get_db)):
    key = f"note:{note_id}"
    try:
        cached = redis_client.get(key)
        if cached:
            return NoteOut.model_validate_json(cached)
    except redis.RedisError:
        log.warning("redis unavailable, reading from database")

    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    out = NoteOut.model_validate(note)
    if out.status == "processed":
        try:
            redis_client.setex(key, 60, out.model_dump_json())
        except redis.RedisError:
            pass
    return out
