# Day 1 & Day 2 — Tasks

Project folder: `D:\HarmonicIQ\cloud-native-learning`
Concepts for Day 1 are in `notes/day-01-notes.md`. Day 2 concepts are in this file.

---

# DAY 1 — Cloud-Native Mindset + 12 Factors (~3 hrs)

## ✅ 1. Setup (20 min)
- [ ] Create an empty GitHub repo named **`cloud-native-30`**
- [ ] Check these files are in your folder: `app.py`, `requirements.txt`, `.gitignore`, `.env.example`, `README.md`, `12-factor-check.md`, `LEARNINGS.md`
- [ ] Enrol in **LFS158: Introduction to Kubernetes** (free, Linux Foundation). Only sign up today; study it on Days 3–6.

## ✅ 2. Learn (1 hr)
- [ ] Read **12factor.net** (one short page per factor)
- [ ] Re-read `notes/day-01-notes.md` (restaurant analogy for all 12)
- [ ] Watch an intro video: **Abhishek Veeramalla** (English) or **Technical Guftgu** (Hindi)
- [ ] Open **landscape.cncf.io** for 10 min. Find: Kubernetes, Helm, Argo, Prometheus, OpenTelemetry.

## ✅ 3. Run the app (30 min) — PowerShell, inside the project folder
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:CELERY_EAGER="true"
uvicorn app:app --reload
```
- [ ] Open **http://localhost:8000/docs**
- [ ] Try `GET /` → you see version and pod (your PC name)
- [ ] Try `GET /healthz` → `{"status": "ok"}`
- [ ] Try `GET /readyz` → **503** (Redis is not running, this is expected)
- [ ] Try `POST /notes` with `{"title": "day 1", "body": "learning twelve factor app"}`
- [ ] Try `GET /notes/1` → `status: processed`, `word_count: 4`
- [ ] Try `GET /notes/99` → **404**

## ✅ 4. 12-factor check (45 min)
- [ ] Open `12-factor-check.md`
- [ ] For each factor write **✅ / ⚠️ / ❌** and **one line why**
- [ ] Fill in the "What to fix later" table (hint: look at factors 5, 10 and 12)

## ✅ 5. Close the day (15 min)
- [ ] Write the Day 1 entry in `LEARNINGS.md`: 3 things learned + 1 open question
- [ ] Push to GitHub:
```powershell
git init
git add .
git commit -m "Day 1: app + 12-factor check"
git branch -M main
git remote add origin https://github.com/<your-username>/cloud-native-30.git
git push -u origin main
```
- [ ] Tick Day 1 in the tracker
- [ ] Answer the self-check questions 5–7 at the end of `day-01-notes.md`

---

# DAY 2 — Containers: Internals, Multi-Stage, Non-Root (~3 hrs)

**Goal today:** build a Docker image of `app.py` that is **small** and runs as **non-root**, and prove it by comparing sizes.

**Before you start:** install **Docker Desktop** for Windows (if not already) and check:
```powershell
docker version
```

## 📖 Concepts (read first, 30 min)

### What is a container, really?
A container is **just a normal process on Linux** with two kinds of limits around it.

🏢 **Analogy: an apartment building**
- The building = one Linux machine (kernel)
- Each flat = one container
- **Namespaces** = the **walls** of the flat. What the process can **see**: its own files, its own network, its own process list. It can't see the neighbours.
- **cgroups** = the flat's **electricity and water meter with a limit**. How much it can **use**: CPU and memory.

```
              One Linux kernel (the building)
┌───────────────────────────────────────────────────────┐
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐  │
│  │ container A │   │ container B │   │ container C │  │
│  │ namespaces: │   │ (own walls) │   │             │  │
│  │ own files,  │   │             │   │             │  │
│  │ network, PID│   │             │   │             │  │
│  │ cgroup:     │   │             │   │             │  │
│  │ 512MB, 0.5CPU│  │             │   │             │  │
│  └─────────────┘   └─────────────┘   └─────────────┘  │
└───────────────────────────────────────────────────────┘
```
👉 This is why containers start in **seconds**: no new operating system boots, only a process starts. A **virtual machine** is a whole separate house; a **container** is a flat in a shared building.

👉 Kubernetes `requests/limits` (Day 6) are just **cgroups** settings.

### Image layers
🧾 **Analogy: transparent sheets stacked on top of each other.** Each Dockerfile line adds one sheet. Docker **reuses (caches)** sheets that didn't change.

```
Layer 4: COPY app.py            ← changes often (rebuilt every time)
Layer 3: RUN pip install        ← changes only when requirements change
Layer 2: COPY requirements.txt
Layer 1: FROM python:3.12-slim  ← almost never changes
```
**Rule:** copy `requirements.txt` and install packages **before** copying your code. Then a code change doesn't reinstall every package, and builds take seconds instead of minutes.

### Multi-stage build
🍕 **Analogy: the kitchen vs the plate.** You cook in a big kitchen full of tools (compilers, pip, cache). You **serve only the pizza on a plate**. The customer doesn't get the oven.

```
Stage 1 "builder"  (big: pip, build tools)  ──► installs packages
                                                     │ copy only the result
Stage 2 "runtime"  (small: only Python)     ◄────────┘  + app.py → final image
```

### Non-root user
🔑 **Analogy:** don't give the cook the **master key of the whole building**. If an attacker breaks into your app, a non-root user limits what they can do. Many Kubernetes clusters **refuse** to run root containers (Day 25: Pod Security).

### Distroless (stretch goal)
🍽️ A plate with **nothing else on it**: no shell, no `apt`, no extra tools. Smaller image, and an attacker has almost no tools to use. The downside: you can't `docker exec ... sh` into it to debug.

## 🎥 Learn (1 hr)
- [ ] Abhishek Veeramalla: **Docker multi-stage builds / distroless** video
- [ ] (Optional) **iximiuz Labs**: container namespaces and cgroups labs
- [ ] (Hindi backup) Technical Guftgu or Train With Shubham Docker video

## 🛠️ Hands-on (1.5 hrs)

### Step 1 — Create `.dockerignore`
Keeps junk and secrets out of the image. Create the file `.dockerignore`:
```
.venv/
venv/
__pycache__/
*.pyc
.env
local.db
.git/
notes/
*.md
```

### Step 2 — Version 1: the naive image (to compare against)
Create `Dockerfile.v1`:
```dockerfile
FROM python:3.12
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```
```powershell
docker build -f Dockerfile.v1 -t cn30:v1-naive .
```
- [ ] Built. Note the problems: big base image, runs as **root**, code copied **before** packages (bad caching).

### Step 3 — Version 2: multi-stage + non-root (your main image)
Create `Dockerfile`:
```dockerfile
# ---------- Stage 1: builder (has pip and build tools) ----------
FROM python:3.12-slim AS builder
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Stage 2: runtime (only what the app needs) ----------
FROM python:3.12-slim
RUN useradd --create-home --uid 10001 appuser
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY app.py .
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
USER 10001
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```
```powershell
docker build -t cn30:v2 .
```
- [ ] Built successfully

### Step 4 — Run it
```powershell
docker run --rm -p 8000:8000 `
  -e CELERY_EAGER=true `
  -e DATABASE_URL=sqlite:////tmp/local.db `
  cn30:v2
```
Why `/tmp/local.db`? The app runs as non-root, so it can't write into `/app`. In Kubernetes you'll use Postgres anyway, and a container's disk is temporary (factor 6).

- [ ] Open http://localhost:8000/docs and repeat the Day 1 endpoint checks
- [ ] `GET /` now shows the **container ID** as the pod name

### Step 5 — Prove it is non-root
In a second PowerShell window:
```powershell
docker ps                              # copy the container ID
docker exec <container-id> whoami      # should print: appuser
docker exec <container-id> id          # should show uid=10001
```
- [ ] `whoami` prints **appuser**, not root

### Step 6 — Compare sizes
```powershell
docker images cn30
```
- [ ] Write both sizes in `LEARNINGS.md` (v1-naive vs v2). v2 should be several hundred MB smaller.

### Step 7 — Test layer caching
- [ ] Change one line in `app.py` (e.g. `APP_VERSION` default to `"v2"`)
- [ ] Run `docker build -t cn30:v2 .` again
- [ ] Notice `pip install` shows **CACHED** and the build is fast. Write this in `LEARNINGS.md`.

### Step 8 — ⭐ Stretch: distroless image
Create `Dockerfile.distroless`:
```dockerfile
FROM python:3.11-slim-bookworm AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/deps -r requirements.txt

FROM gcr.io/distroless/python3-debian12:nonroot
WORKDIR /app
COPY --from=builder /deps /deps
COPY app.py .
ENV PYTHONPATH=/deps PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```
Python **3.11** here because distroless Debian 12 ships Python 3.11, so the builder must match.
```powershell
docker build -f Dockerfile.distroless -t cn30:v3-distroless .
docker run --rm -p 8000:8000 -e CELERY_EAGER=true -e DATABASE_URL=sqlite:////tmp/local.db cn30:v3-distroless
docker exec <container-id> sh          # fails: there is no shell. That's the point.
```
- [ ] Compare the size of all three images

## ✅ Close the day (15 min)
- [ ] Day 2 entry in `LEARNINGS.md`: 3 things learned, the image size table, 1 open question
- [ ] Push:
```powershell
git add .
git commit -m "Day 2: multi-stage non-root Dockerfile"
git push
```
- [ ] Tick Day 2 in the tracker

## ✍️ Day 2 self-check
1. What is the difference between **namespaces** and **cgroups**? (Use the apartment analogy.)
2. Why do we copy `requirements.txt` **before** `app.py` in the Dockerfile?
3. In a multi-stage build, what goes into the **final** image, and what is left behind?
4. Why is running a container as **root** a risk?
5. Distroless has no shell. What is one advantage and one disadvantage?

---

**If any command fails, copy the full error message and send it to me.**
