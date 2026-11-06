# Cloud-Native 30 — Learnings

One short entry per day. 3 things learned + 1 open question. Commit every day.

---

## Day 1 — Cloud-native mindset + 12-factor app
**Date:** 2026-10-29

**What I learned**
1. The 12-factor app treats **config as environment variables**, not hardcoded values — `app.py` reads `DATABASE_URL`, `REDIS_URL`, `APP_VERSION` from `os.getenv` so the same image can run in dev, staging, and prod.
2. **Logs go to stdout** (factor 11), not to a file. The app just does `logging.basicConfig(...)` and lets Kubernetes collect the stream — this is why Loki/Grafana work later (Day 23).
3. The app is **stateless** (factor 6): no files written to disk, state lives in Postgres and Redis. That's what lets Kubernetes kill and restart a pod anywhere without losing data.

**Open question**
- `/readyz` returned 503 because Redis isn't running — in Kubernetes, how does a readiness probe failure actually affect traffic routing? Does the pod get removed from the Service, or does it keep retrying?

**Proof**
- Ran `app.py` locally and tried all endpoints at `/docs`
- Filled in `12-factor-check.md`
- Pushed Day 1 commit to GitHub

---

## Day 2 — Containers: multi-stage, non-root
**Date:** 2026-10-31

**What I learned**
1. **Multi-stage builds** keep build tools (pip, cache) out of the final image — the builder stage installs packages, the runtime stage copies only the venv. My `cn30:v2` is **77 MB** vs naive `cn30:v1-naive` at **471 MB** — 6x smaller.
2. **Non-root user** is a Dockerfile one-liner (`useradd --uid 10001 appuser` + `USER 10001`) but prevents a whole class of container escapes. Verified with `docker exec <id> whoami` → `appuser`, `id` → `uid=10001`. Kubernetes Pod Security (Day 25) will reject root containers.
3. **Layer caching order matters a lot**. Copying `requirements.txt` + `pip install` BEFORE `COPY app.py .` means an `app.py` change doesn't re-run pip. Rebuild dropped from ~2 min → ~5 sec.

**Image size comparison**
| Image | Content size | Why |
|---|---|---|
| `cn30:v1-naive` | 471 MB | full `python:3.12`, root, `COPY . .` first |
| `cn30:v2` | 77 MB | `python:3.12-slim`, multi-stage, non-root, caching-friendly |

**Open question**
- `/readyz` returned 503 because Redis isn't running inside my container (CELERY_EAGER=true skips the real worker). This is actually what readiness probes are *supposed* to do — database check passed, Redis check failed → Kubernetes would remove the pod from the Service until Redis is back. Readiness ≠ liveness. Full Redis + worker properly comes on Day 7 with Docker Compose.

**Proof**
- Built `cn30:v1-naive` and `cn30:v2` images
- Ran `cn30:v2` container, tested endpoints at `http://localhost:8000/docs`
- Verified non-root: `whoami` = `appuser`, `id` = `uid=10001(appuser)`
- Confirmed layer caching: `app.py` change triggered only the last `COPY` layer on rebuild
