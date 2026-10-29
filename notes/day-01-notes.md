# Day 1 — Cloud-Native Mindset & the 12-Factor App

> **Big idea:** a traditional server is a **pet** (named, fixed by hand). A cloud-native app is **cattle** (identical copies, replaced automatically). The 12 factors are the rules that make your app "cattle".

```
Pet server                      Cattle (cloud-native)
┌──────────┐                    ┌───┐ ┌───┐ ┌───┐
│ server-1 │ ← fix by hand      │pod│ │pod│ │pod│ ← identical, replaceable
│ config   │                    └───┘ └───┘ └───┘
│ inside   │                    config from env, state in DB/Redis
└──────────┘
```

**Analogy used throughout:** your app is a **restaurant chain** (like Domino's). One recipe, many branches, and every branch must work the same way. Kubernetes is the company that opens and closes branches automatically.

---

## Part 1 — How the app is *made* (factors 1–4)

### 1. Codebase: one repo, many deploys
🍕 One **recipe book** for every branch.

```
          one Git repo
              │
   ┌──────────┼──────────┐
   ▼          ▼          ▼
  dev      staging     prod      ← same code, different deploys
```
- ❌ `app-prod/` and `app-dev/` folders with copied code that slowly become different.
- ✅ One repo. Dev, staging and prod deploy different versions of it.

### 2. Dependencies: declare everything explicitly
🍕 The recipe lists **exact ingredients**, not "whatever cheese is in the kitchen".
- ❌ Works on your laptop only because you once ran `pip install redis` by hand.
- ✅ Every package pinned in `requirements.txt` (`fastapi==0.115.6`).

### 3. Config: store config in the environment
🍕 Each branch's **address and phone number** are kept outside the recipe book.

**Config** = anything that changes between dev and prod: DB URL, passwords, API keys.

```python
# ❌ Bad: password in Git
DATABASE_URL = "postgresql://admin:Pass123@prod-db:5432/app"

# ✅ Good: read from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")
```
**Test:** could you make your repo public right now without leaking a password? If yes, config is in the right place.

### 4. Backing services: treat them as attached resources
🍕 A **supplier** is just a phone number. Swap Supplier A for B without changing the recipe.

**Backing service** = anything you talk to over the network: Postgres, Redis, S3, email APIs.
```
REDIS_URL=redis://localhost:6379/0                 # laptop
REDIS_URL=redis://my-cache.xyz.amazonaws.com:6379  # AWS
```
To move Redis to AWS you change the **env var, not the code**.

---

## Part 2 — How the app *runs* (factors 5–8)

### 5. Build, release, run: keep the three stages separate
🍕 The **central kitchen** makes the base; branches never change the base at the counter.

```
 BUILD                    RELEASE                     RUN
 code ──► Docker image ──► image + env config ──► running pods
          (cn30:v1.2)      (v1.2 + prod env)
```
- ❌ SSH into prod and edit `app.py` directly.
- ✅ Fix code → commit → build image `v1.3` → deploy. Broken? Roll back to `v1.2`.

**Why SSH-fixing breaks on Kubernetes:**
```
Git repo / image v1.2 (bug)      Pod A  ← you SSH in and fix it ✏️
                                 Pod B  ← still has the bug
                                 Pod C  ← still has the bug
Pod A restarts → K8s recreates it from image v1.2 → your fix is GONE
```
1. Only one pod is fixed. 2. The fix disappears on restart. 3. No record in Git: no review, no rollback.

### 6. Processes: the app is stateless
🍕 A chef writes orders on the **order board**, not in his head.

```python
# ❌ Bad
sessions = {}                          # lives in THIS pod's memory only
open(f"/app/uploads/{name}", "wb")     # file saved on THIS pod's disk

# ✅ Good
redis_client.setex(f"cart:{user_id}", 3600, cart_json)  # any pod can read it
s3.upload_fileobj(file, "my-bucket", name)              # survives pod death
```
**Cart in a `dict` with 3 pods:**
```
Request 1: "Add phone to cart"  ──► Pod A   dict = {ayush: [phone]}
Request 2: "Show my cart"       ──► Pod B   dict = {}            → "Cart is empty!"
Request 3: "Show my cart"       ──► Pod A   dict = {ayush: [phone]} → phone is back!
Pod A restarts                  ──► Pod A   dict = {}            → phone gone forever
```

### 7. Port binding: the app serves HTTP itself
🍕 Each branch has **its own front door**.
- ❌ App only works when dropped into an Apache/Tomcat already on the server.
- ✅ `uvicorn app:app --host 0.0.0.0 --port 8000`. Kubernetes just sends traffic to port 8000.

### 8. Concurrency: scale out with more processes
🍕 Busy Friday → **more chefs and more delivery boys**, added separately.

```
             scale OUT (more copies), by process TYPE
 web (API)       [pod][pod][pod][pod]   ← many users → add API pods
 worker (Celery) [pod][pod]             ← long queue → add worker pods
```
- ❌ One huge server; buy a bigger one when load grows (scale up).
- ✅ Run more copies of each process type. On Day 10, KEDA adds worker pods when the Redis queue grows.

---

## Part 3 — How the app *behaves in production* (factors 9–12)

### 9. Disposability: start fast, stop politely
🍕 A delivery boy starts his shift in 1 minute and **finishes the current delivery** before going home.

```
K8s: "Pod, please stop" (SIGTERM)
 │
 ├─ ✅ Good app: stop taking new requests → finish current ones → exit
 └─ ❌ Bad app:  dies instantly → user gets an error mid-request
```
In `app.py`: `task_acks_late=True` means a task from a dead worker goes back to the queue and another worker retries it.

### 10. Dev/prod parity: keep dev and prod similar
🍕 The **training kitchen** uses the **same oven** as the real branch.
- ❌ SQLite on laptop, Postgres in prod → queries fail only in prod.
- ✅ Same Postgres/Redis locally (Docker or kind), same Docker image everywhere.

### 11. Logs: write to stdout
🍕 The chef doesn't keep a **private diary**; the manager keeps **one central register**.
```
Pod A ─stdout─┐
Pod B ─stdout─┼──► Loki / CloudWatch ──► search all logs in one place
Pod C ─stdout─┘
```
- ❌ Writing to `/var/log/app.log` inside the pod: lost when the pod dies, and 10 pods means 10 places to check.
- ✅ Print to stdout; the platform collects it.

### 12. Admin processes: run one-off tasks the same way as the app
🍕 The **monthly deep-clean** is a separate job using the standard kit, not done during service.
- ❌ `create_all()` at startup in every pod (3 pods change the DB at once), or running migrations from your laptop.
- ✅ Run `alembic upgrade head` once, as a **Kubernetes Job**, with the same image and config (Day 9).

---

## All 12 on one page 🍕

| # | Factor | Analogy | Rule |
|---|---|---|---|
| 1 | Codebase | one recipe book | one repo, many deploys |
| 2 | Dependencies | exact ingredient list | pin everything |
| 3 | Config | address outside the recipe | env vars, never in code |
| 4 | Backing services | suppliers are phone numbers | attach by URL, swap via env |
| 5 | Build, release, run | central kitchen makes the base | never edit running code |
| 6 | Processes | orders on the board | stateless; data in DB/Redis/S3 |
| 7 | Port binding | own front door | app serves its own port |
| 8 | Concurrency | more chefs on Friday | scale out, per process type |
| 9 | Disposability | finish the delivery first | fast start, graceful stop |
| 10 | Dev/prod parity | same oven | same services everywhere |
| 11 | Logs | one central register | write to stdout |
| 12 | Admin processes | deep-clean as a separate job | one-off Job, same image |

---

## Bonus — What is SSH?

**SSH (Secure Shell)** lets you open a terminal on another computer over the internet, safely. 📺 Like a TV remote with a secret, locked signal.

```
 Your laptop                       Internet                    Server (e.g. AWS EC2)
┌────────────┐                                               ┌──────────────────┐
│ $ ls       │ ════════ encrypted tunnel (port 22) ════════► │ runs "ls" here   │
│            │ ◄═══════ result comes back encrypted ════════ │ sends output back│
└────────────┘                                               └──────────────────┘
   SSH client                                                    SSH server (sshd)
```

**Three parts:**
1. **Client and server:** `ssh` on your laptop; `sshd` on the server, listening on **port 22** (open it in the AWS Security Group).
2. **Encryption:** nobody in between can read your traffic (Telnet, the old tool, sent plain text).
3. **Authentication:** password (weak) or **key pair** (standard).

**Key pair = padlock and key 🔐**
- **Public key** (`id_ed25519.pub`) = padlock. Safe to share; it goes on the server in `~/.ssh/authorized_keys`.
- **Private key** (`id_ed25519` / AWS `.pem`) = the only key. **Never leaves your laptop.**

**Login flow:** server says "sign this random message" → your laptop signs it with the private key (the key is never sent) → server checks with the public key → you're in.

```bash
ssh-keygen -t ed25519 -C "ayush@laptop"        # create a key pair
ssh -i key.pem ec2-user@13.233.45.10           # log in to EC2
scp app.py ec2-user@13.233.45.10:/home/ec2-user/   # copy a file
chmod 400 key.pem                              # fix "permissions too open"
```
**Timeout when connecting to EC2?** First check that the Security Group allows **port 22** from your IP.

**SSH in the cloud-native world:**

| Old way (SSH) | Cloud-native way |
|---|---|
| SSH in and edit code | Git commit → new image → deploy |
| SSH in to read logs | stdout → Loki / CloudWatch |
| SSH in to debug | `kubectl logs`, `kubectl exec` (look, don't fix) |
| Port 22 open to the internet | Port 22 closed; AWS SSM Session Manager if needed |

SSH is fine for learning and one-off checks, but never for **changing** production.

---

## Day 1 checklist

**Setup**
- [ ] GitHub repo `cloud-native-30` created
- [ ] `app.py`, `requirements.txt`, `.gitignore`, `.env.example`, `README.md` added
- [ ] Enrolled in **LFS158: Introduction to Kubernetes** (free, Linux Foundation)

**Learn**
- [ ] Read 12factor.net
- [ ] Watched an intro video (Abhishek Veeramalla, or Technical Guftgu in Hindi)
- [ ] Explored landscape.cncf.io: found Kubernetes, Helm, Argo, Prometheus, OpenTelemetry

**Hands-on**
- [ ] Ran `app.py` locally and tried every endpoint at `/docs`
- [ ] Filled in `12-factor-check.md`

**Close**
- [ ] Day 1 entry in `LEARNINGS.md`
- [ ] `git commit` + `git push`
- [ ] Ticked Day 1 in the tracker

## Self-check questions
1. Teammate puts the AWS secret key in `settings.py`. Which factor is broken? *(#3 Config: key leaks via Git, and changing environments needs code changes)*
2. Moving Redis to ElastiCache: change code or env var? *(Env var, #4 Backing services)*
3. Cart stored in a Python `dict`, 3 pods. What do users see? *(Cart appears and disappears; lost on restart. #6 Processes)*
4. "Just SSH in and fix the file." Why is this bad? *(Only one pod fixed, fix lost on restart, no Git record. #5 Build, release, run)*
5. Logs written to `/app/logs/app.log` inside the pod. Problem?
6. K8s wants to stop a pod. What should a good app do?
7. SQLite on laptop, Postgres in prod. Which factor is broken?
