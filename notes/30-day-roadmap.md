# Cloud-Native in 30 Days — Roadmap

One project for all 30 days: a **FastAPI + PostgreSQL + Redis + Celery** app, taken from a local Kubernetes cluster to a GitOps-driven platform on AWS EKS.

```
Week 1            Week 2              Week 3                 Week 4
K8s Core   ──►   K8s Production ──►  IaC + GitOps on AWS ──► Observe, Secure, Platform
(local kind)     (Helm, scaling)      (Terraform, EKS, Argo)  (OTel, policies, tenancy)
   │                  │                    │                       │
   ▼                  ▼                    ▼                       ▼
App runs on K8s   App is a Helm chart  git push → live on EKS   Production-grade platform
   25%                50%                  75%                     100%
```

---

## Daily rhythm (~3 hrs)

```
30 days × ~3 hrs = ~90 hrs total
├── Watch (YouTube / LFS158)   ~30 hrs  (1 hr/day)
├── Hands-on project           ~55 hrs  (2 hrs/day)  ← proof for BambooHR
└── Notes + demos              ~5 hrs   (10 min/day + 3 short videos)
```
- Watch at **0.75x** with **English subtitles**. If stuck, watch the same topic in Hindi first.
- End each day with one entry in `LEARNINGS.md`, then `git commit` + `git push`.
- **Busy day?** Skip the video and do 30 min of hands-on. The repo matters more than the videos.

## Main resources

| Resource | Language | Use for |
|---|---|---|
| **Abhishek Veeramalla** (YouTube) | Simple Indian English | Main channel, all 4 weeks |
| **Technical Guftgu** / **Train With Shubham** | Hindi | Backup when a topic is unclear |
| **Kubesimplify** (Saiyam Pathak) | Simple Indian English | KEDA, Kyverno, OpenTelemetry, vcluster |
| **TechWorld with Nana** | Clear English | Helm, Terraform, StatefulSets |
| **That DevOps Guy** | Clear English | Prometheus |
| **LFS158** (Linux Foundation) | English, free | Week 1 + free Credly badge |
| **Killercoda** | — | Free Kubernetes labs in the browser |
| **HashiCorp tutorials**, **EKS Workshop** | — | Week 3 |

---

## Week 1 — Kubernetes Core (local, kind)
**Goal:** the whole app runs on a local cluster, and you earn the LFS158 badge.

| Day | Topic | Build | Learn |
|---|---|---|---|
| 1 | Cloud-native mindset: 12-factor apps, CNCF landscape | Create the repo; check `app.py` against the 12 factors | 12factor.net · Abhishek intro · enrol in LFS158 |
| 2 | Container internals: namespaces, cgroups, multi-stage and distroless images | Write a small, non-root Dockerfile | iximiuz Labs · Abhishek "Docker multi-stage / distroless" |
| 3 | K8s architecture: API server, etcd, scheduler, controllers, kubelet | Create a kind cluster; explore with `kubectl` | LFS158 "Kubernetes Architecture" · Kunal Kushwaha K8s course |
| 4 | Pods, Deployments, ReplicaSets, rolling updates | Deploy FastAPI; roll out and roll back a version | LFS158 "Deployments" · Abhishek K8s series |
| 5 | Services, Ingress, cluster DNS | Expose the API through ingress-nginx | Abhishek (Services, Ingress) · Killercoda playground |
| 6 | ConfigMaps, Secrets, probes, requests/limits | Wire `/healthz` + `/readyz` probes and resource limits; finish LFS158 | LFS158 remaining chapters · Nana "Kubernetes probes" |
| 7 | 🏁 **Checkpoint** | API + Postgres + Redis + Celery worker all running on kind | Technical Guftgu (Hindi) to revise |

**Proof:** repo link · `kubectl get pods` screenshot · LFS158 Credly badge

---

## Week 2 — Kubernetes Production Patterns
**Goal:** the app is one Helm chart that scales and survives failures.

| Day | Topic | Build | Learn |
|---|---|---|---|
| 8 | StatefulSets, PV/PVC, StorageClass | Move Postgres to a StatefulSet with a PVC; note why prod uses RDS | kubernetes.io StatefulSet tutorial · Nana "StatefulSet explained" |
| 9 | Jobs and CronJobs | Run Alembic migrations as a Job; compare CronJob with Celery beat | kubernetes.io Jobs docs · Abhishek K8s series |
| 10 | Autoscaling: HPA, metrics-server, KEDA | Scale Celery workers on Redis queue length with KEDA | Kubesimplify "KEDA" · keda.sh Redis scaler docs |
| 11 | RBAC, ServiceAccounts, NetworkPolicies | Allow only API pods to reach Postgres | Abhishek "Kubernetes RBAC" · Killercoda NetworkPolicy |
| 12 | Helm: charts, values, templating | Package the whole app as one Helm chart | Nana "Helm explained" · helm.sh Chart Template Guide |
| 13 | Kustomize and environment overlays | Create dev, staging and prod overlays | kubernetes.io Kustomize docs |
| 14 | 🏁 **Checkpoint + debugging drill** | Break it on purpose (CrashLoopBackOff, OOMKilled, ImagePullBackOff) and fix it | Killercoda troubleshooting scenarios |

**Proof:** repo link (Helm chart) + short note of what you fixed

---

## Week 3 — Infrastructure as Code + GitOps on AWS
**Goal:** `git push` leads to a deployment on EKS.
⚠️ **Cost:** EKS is not free. Run `terraform destroy` at the end of every session.

| Day | Topic | Build | Learn |
|---|---|---|---|
| 15 | Terraform: providers, state, modules, remote state | Set up an S3 backend with state locking | HashiCorp "Get Started – AWS" · Nana Terraform course |
| 16 | Terraform for VPC and EKS | Provision a VPC and EKS with terraform-aws-modules | Abhishek "Terraform Zero to Hero" · terraform-aws-modules/eks |
| 17 | EKS specifics: Pod Identity/IRSA, AWS LB Controller, EBS CSI | Let a pod read from S3 without static keys | eksworkshop.com · AWS EKS Pod Identity docs |
| 18 | CI: GitHub Actions, Trivy scanning, ECR | Build, test, scan and push on every commit | Abhishek "GitHub Actions" · Trivy docs |
| 19 | GitOps with Argo CD (app-of-apps) | Make Argo CD sync your Helm chart from Git | Abhishek "Argo CD" · Argo CD Getting Started |
| 20 | Progressive delivery with Argo Rollouts | Canary release of a new API version | Argo Rollouts docs · Kubesimplify |
| 21 | 🏁 **Checkpoint** | `git push` → live on EKS, then `terraform destroy` | Record a demo while it runs |

**Proof:** 5-minute demo video link

---

## Week 4 — Observability, Security, Platform
**Goal:** a production-grade platform you can explain end to end.

| Day | Topic | Build | Learn |
|---|---|---|---|
| 22 | Metrics: Prometheus and PromQL | Instrument FastAPI; track rate, errors, latency | That DevOps Guy "Prometheus" · prometheus-fastapi-instrumentator |
| 23 | Tracing and logs: OpenTelemetry, Tempo, Loki | Trace one request from the API through a Celery task | OpenTelemetry Python docs · Kubesimplify OTel |
| 24 | SLOs, alerting, dashboards | Define one SLO and alert on burn rate | Google SRE Workbook "Implementing SLOs" (free) |
| 25 | Security: Pod Security, Kyverno, External Secrets, cosign | Block unsigned images; pull secrets from AWS Secrets Manager | Kubesimplify "Kyverno" · External Secrets docs |
| 26 | *(optional)* Service mesh basics (Linkerd), mTLS | Turn on mTLS; note when a mesh is not worth it | Linkerd Getting Started |
| 27 | *(optional)* Multi-tenancy: namespace-per-tenant, quotas, vcluster | Onboard two tenants with isolation and quotas | vcluster docs · Kubesimplify |
| 28 | Reliability and cost: PDBs, Karpenter, spot, chaos | Kill nodes and pods; watch it recover | Karpenter docs |
| 29 | 🏁 **Capstone** | Bring all pieces together; write a one-page architecture doc | Your own `LEARNINGS.md` |
| 30 | 🏁 **Review and demo** | Timed troubleshooting drill; demo to your team; set BambooHR to 100% | Killercoda CKAD scenarios |

**Proof:** architecture doc link + team demo

---

## BambooHR goal

**Title:** Build cloud-native platform skills: Kubernetes, Terraform, GitOps and observability on AWS

**Description:** Complete a 30-day hands-on program to deploy and operate our backend stack (FastAPI, PostgreSQL, Redis, Celery) the cloud-native way: Kubernetes, Helm, Terraform-provisioned EKS, Argo CD GitOps, and Prometheus/OpenTelemetry observability. **Outcome:** a working reference setup and an architecture document the team can reuse. **Evidence:** GitHub repo with daily notes, demo video, architecture doc.

| Due | Milestone | Proof | % |
|---|---|---|---|
| Day 7 | App running on local Kubernetes + LFS158 badge | Repo link, `kubectl get pods` screenshot, Credly badge | 25 |
| Day 14 | Helm chart with autoscaling, RBAC, network policies | Repo link + short note | 50 |
| Day 21 | EKS via Terraform; `git push` deploys via Argo CD | 5-min demo video | 75 |
| Day 30 | Monitoring, tracing, security + architecture doc shared | Doc link + team demo | 100 |

---

## If you fall behind
1. Cut **Day 26** (service mesh) and **Day 27** (multi-tenancy) first.
2. **Never cut** Terraform, Argo CD or monitoring. Your milestones depend on them.
3. Merge days rather than skip them. Weeks 1–2 are the foundation for everything after.

## After Day 30 (optional)
- **KCNA** (entry-level cert) → **CKAD** → **CKA**, plus **HashiCorp Terraform Associate**
- Ask your manager whether the company pays for certification exams.
