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
