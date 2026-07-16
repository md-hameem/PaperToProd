# PaperToProd — Document 11: Infrastructure

**Status:** Draft v1.0

---

## 1. Cloud Provider Choice

**Primary: AWS.** Rationale: most mature GPU-instance availability/spot-market depth (critical given per-job GPU demand for validation runs, Document 8 §3.5), broadest managed-Kubernetes (EKS) maturity, and the deepest bench of Terraform provider coverage for the ancillary services this platform needs (managed Postgres via RDS, managed Redis via ElastiCache, S3 for object storage — MinIO is used for local/dev parity and as an abstraction layer, but production storage targets S3 directly).

**Multi-cloud posture:** Explicitly *not* multi-cloud at launch — the operational overhead of multi-cloud (Azure/GCP/OCI) is not justified until a specific enterprise customer's data-residency or existing-cloud-commitment requirement demands it (a realistic future trigger, especially for enterprise deals — Document 15/16 flag this as a re-evaluation point, not a v1 requirement). Self-hosted/on-prem is offered only as a Document 12-compliant enterprise option (VPC-peered or fully on-prem deployment via the same Helm charts used for the managed service), not a first-class parallel platform.

## 2. Container Orchestration: Kubernetes (EKS)

- **Node pools, explicitly separated by workload profile** (directly mirroring Document 9's service boundaries):
  - `api-pool` — CPU, general-purpose instances, autoscaled on request latency/CPU.
  - `worker-pool` — CPU, higher-memory instances (LangGraph/LLM-I/O-bound orchestration, Document 8), autoscaled on Celery queue depth.
  - `gpu-pool` — GPU instances (e.g., A10G/L4-class for most reproduction validation; larger A100-class available as an enterprise/higher-tier option for bigger papers), autoscaled on the GPU-specific Celery queue depth (Document 9 §5), using cluster-autoscaler with a GPU-aware scaling policy to avoid over-provisioning expensive idle GPU nodes.
  - `sandbox-pool` — CPU (and GPU where required), running the Sandboxed Execution Service (Document 12) with the strictest network-policy isolation of any pool — no pod-to-pod traffic permitted to any other pool by default.

## 3. Helm

- Each service (api, worker, sandbox-svc) ships as its own Helm chart, parameterized for environment (dev/staging/prod) rather than maintaining separate manifests per environment — environment-specific values live in `values-{env}.yaml` overlays, keeping the chart templates themselves environment-agnostic (a maintainability requirement given this is a small early engineering team who cannot afford chart drift across environments).

## 4. Terraform

- All cloud resources (VPC, EKS cluster, RDS, ElastiCache, S3 buckets, IAM roles, GPU node group configuration) defined in Terraform, organized as environment-scoped root modules composing shared reusable modules (`modules/eks-node-pool`, `modules/rds-postgres`, etc.) — this reuse is what makes standing up an isolated enterprise/on-prem-adjacent deployment (per §1) a parameterization exercise rather than a bespoke rebuild.

## 5. CI/CD: GitHub Actions

- **Pipeline stages:** lint/typecheck → unit tests → build container images → integration tests (against ephemeral environment) → security scan (Document 12, dependency + container scanning) → deploy to staging (automatic on merge to main) → deploy to production (manual approval gate, or automatic for low-risk changes per a defined change-classification policy).
- **Golden Dataset regression gate (Document 8 §9):** any change touching agent prompts or the orchestration graph additionally runs the Golden Dataset evaluation suite in CI, blocking deploy on Fidelity Score regression — this is a PaperToProd-specific CI gate beyond standard software CI, reflecting that this product's core risk is agent-behavior regression, not just code-correctness regression.

## 6. Secrets Management

- AWS Secrets Manager (or HashiCorp Vault for the on-prem/enterprise deployment variant) for all credentials (DB connection strings, LLM API keys, GitHub App private keys, customer BYO-API-keys per Document 9 §7) — injected into pods via a secrets-store CSI driver, never baked into container images or committed configuration, and rotated on a defined schedule with automatic pod restart on rotation.

## 7. Monitoring: Prometheus, Grafana, OpenTelemetry

- **OpenTelemetry** as the single instrumentation standard across api/worker/sandbox-svc (traces + metrics + logs), avoiding vendor-specific SDKs that would lock the observability layer to one backend.
- **Prometheus** scrapes OTel-exported metrics; **Grafana** dashboards split by audience: an engineering-ops dashboard (latency, error rate, queue depth, GPU utilization) and a product dashboard (Document 1 §11/12 metrics: reproduction success rate, fidelity score distribution, time-to-runnable) — same underlying metric pipeline, different curated views, avoiding a second parallel analytics stack for what's fundamentally operational data.
- **Alerting:** Alertmanager rules on queue-depth thresholds (predicting NFR-PERF-03 breach before it happens, not just after), GPU-pool saturation, and repair-loop exhaustion rate spikes (a leading indicator of an agent-quality regression, complementing the CI-time Golden Dataset gate with a production-time signal).

## 8. Disaster Recovery

- **RPO (Recovery Point Objective):** ≤ 5 minutes for Postgres (continuous WAL shipping, Document 10 §8); ≤ 24 hours for object storage (versioned, cross-region replicated buckets).
- **RTO (Recovery Time Objective):** ≤ 1 hour for full-region failover of the core API/worker path via a warm-standby region (Terraform-defined, not manually provisioned during an incident) — GPU-pool capacity in the standby region is intentionally provisioned smaller (cold-start/scale-up on failover) given GPU cost, since DR for the compute-heavy validation path can tolerate a longer RTO than the core "user can log in and see their data" path.

## 9. High Availability

- Multi-AZ RDS (Postgres) with automatic failover; multi-AZ EKS node groups; API/worker pools run a minimum replica count (never scaled to zero) even during low traffic to avoid cold-start latency on the very first request after a quiet period, which would undermine NFR-PERF-01's 10-second first-progress-update target.

## 10. Cost Optimization

- **GPU spend is the dominant infra cost risk** given the business model (Document 1 §9's usage-based pricing must track this closely): spot/preemptible GPU instances used for the validation workload wherever a paper's job tolerates a possible sandbox restart (the Reviewer agent's repair loop, Document 8, is already designed to be resumable/idempotent, which is precisely what makes spot-instance interruption tolerable here rather than a reliability risk).
- Reserved/savings-plan commitment for the steady-state CPU pools (api/worker), where load is more predictable than the spikier GPU validation workload.
- Idle-GPU-node scale-to-zero during low-traffic windows (with the accepted cold-start tradeoff against NFR-PERF-02's time-to-runnable target — mitigated by keeping a small non-zero warm floor sized to typical off-peak demand, tuned from observed traffic rather than a fixed guess).

## 11. GPU Scheduling

- Kubernetes device-plugin-based GPU scheduling with a dedicated `gpu-pool` node taint/toleration so only GPU-requiring Celery tasks (Document 9 §5) land there — the scheduler additionally bin-packs by GPU-memory-class request (a small-architecture paper's validation doesn't need an A100-class node) to avoid over-allocating expensive GPU classes to jobs that don't need them, directly supporting the cost-optimization goals in §10.

---
*End of Document 11. Proceeding next to Document 12: Security Architecture.*
