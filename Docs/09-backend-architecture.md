# PaperToProd — Document 9: Backend Architecture

**Status:** Draft v1.0

---

## 1. Architectural Style: Modular Monolith (with two extracted services)

**Decision:** Start as a modular monolith (single FastAPI codebase, cleanly separated modules with enforced boundaries) rather than microservices, with two deliberate exceptions extracted as separate services from day one: the **Agent Orchestration Worker** (runs the LangGraph pipeline, Document 8) and the **Sandboxed Execution Service** (runs untrusted generated code, Document 12).

**Rationale (tradeoffs, as required):**
- A pre-PMF product benefits far more from single-codebase deploy simplicity, shared-transaction consistency, and low cross-service-call overhead than from microservices' independent-scaling benefit, which isn't yet needed at this stage.
- The two exceptions are extracted **not** for organizational/team-boundary reasons (the usual microservices justification) but for genuinely distinct **resource and security profiles**: agent orchestration is long-running, LLM-I/O-bound, and needs independent horizontal scaling from the request/response API; sandboxed execution needs strict network/resource isolation (Document 12) that must never share a process boundary with the main API for any reason, security or otherwise.
- Module boundaries within the monolith are enforced via clean internal API contracts (not just informal convention) so that extracting further services later (e.g., Finder's GitHub-search logic, if it becomes a bottleneck) is a boundary-preserving refactor, not a rewrite — directly satisfying NFR-MAINT-01/02.

## 2. Core Modules (within the monolith)

- **Auth & Accounts:** OAuth flows, session/JWT issuance, workspace/RBAC logic (FR-ACC-01–04).
- **Jobs:** job lifecycle CRUD, quota enforcement pre-submission (Document 3's pre-flight quota check), job history queries (paginated per Document 3 §6's scale requirement).
- **Billing:** usage metering ingestion (from the orchestration worker's `audit_log` token/compute counts), plan enforcement, Stripe (or equivalent) integration.
- **Integrations:** GitHub App installation management, BYO-API-key storage (encrypted, Document 12).
- **Gallery:** public-gallery CRUD, respecting the opt-in/erasure rules from Document 3 §11.
- **Notifications:** job-complete email/webhook dispatch.

## 3. REST APIs

FastAPI, versioned under `/api/v1/`, resource-oriented per Document 14's full spec. Key resources: `jobs`, `workspaces`, `members`, `integrations`, `api-keys`, `gallery`. All list endpoints support cursor-based pagination (not offset-based, to remain stable under concurrent writes to fast-growing tables like `jobs`).

## 4. WebSockets

- `/ws/jobs/{job_id}` — authenticated, scoped to a single job, streams `JobState` deltas (agent transitions, log lines, approval-checkpoint prompts) as they're written by the orchestration worker, decoupling the worker (which never talks to clients directly) from the API layer (which owns all client-facing connections).
- **Delivery mechanism:** orchestration worker publishes state-delta events to a Redis pub/sub channel keyed by `job_id`; the API layer's WebSocket handler subscribes to that channel per active connection — this decoupling means the orchestration worker has zero knowledge of connected clients, simplifying its failure/restart semantics (Document 8 §4's checkpointing) since it never needs to manage a client connection's lifecycle.
- **Reconnection:** client-side fallback to polling `GET /jobs/{id}` on socket drop (Document 3 §3 edge case) is mirrored server-side by the fact that `JobState` is always fully queryable via REST regardless of WebSocket connectivity — the socket is a convenience/latency optimization, never the source of truth.

## 5. Background Workers & Task Queues

- **Celery** (with Redis as broker) for the orchestration worker pool — each job's LangGraph execution runs as a Celery task, with LangGraph's own checkpointing (Document 8 §4) providing resumability independent of Celery's own retry semantics (the two are complementary, not redundant: Celery handles worker-process-level retry/dead-lettering, LangGraph handles graph-node-level state resumption).
- **Queue prioritization:** separate Celery queues per plan tier (enterprise jobs get a higher-priority queue) — directly implements the "no queueing delay beyond 2 minutes" NFR (Document 2 NFR-PERF-03) for paying tiers first, with best-effort for free/trial tiers.
- **GPU-requiring jobs** route to a distinct Celery queue consumed only by GPU-capable worker nodes (Document 11), separating GPU-bound work from the much larger pool of CPU-only orchestration steps (Extractor/Finder/DevOps-file-generation don't need GPU; only the Reviewer's actual execution step for GPU-requiring papers does).

## 6. Caching

- **Redis** for: session/JWT blacklist, rate-limit counters, Finder's cross-job search-result cache (Document 8 §3.2), and WebSocket pub/sub (§4).
- **Qdrant** (vector store) doubles as both Finder's similarity-search index (Document 8) and, longer-term, a semantic cache for "has a similar paper already been processed" detection to reduce redundant Extractor work across users submitting closely related papers.

## 7. Authentication & Authorization

- **AuthN:** OAuth (GitHub/Google) + email/password, short-lived JWT access tokens + refresh tokens (httpOnly cookies for web client).
- **AuthZ / RBAC:** Owner/Admin/Member/Billing-only roles (FR-ACC-02) enforced via a single shared authorization-decision module consumed by every endpoint (not per-endpoint ad hoc checks) — this is a security-relevant maintainability decision: a single point of RBAC logic is auditable and testable once, rather than trusting every endpoint author to reimplement the same checks correctly.
- **API keys** (personal, for programmatic job submission per Document 14) are scoped to the issuing user's permissions at time of use (re-checked per request, not cached at key-creation time), so a permission downgrade takes effect immediately even for existing keys.

## 8. Audit Logs

- Enterprise-tier workspaces get a durable, queryable audit log (distinct table, append-only, Document 10) covering: auth events, job submissions, membership/role changes, billing changes, and integration changes — separate from (but cross-referenced with) the AI-agent-level `audit_log` in `JobState` (Document 8 §10), since these serve different audiences (a compliance reviewer vs. an ML engineer debugging a repair loop).

## 9. API Gateway

- A managed API gateway/ingress (cloud-provider-native or Kong/similar, Document 11) handles TLS termination, coarse-grained rate limiting (per-IP, pre-auth), and routing to the appropriate backend service (monolith API vs. WebSocket handler vs. static asset CDN) — application-level rate limiting (per-user/per-plan quotas) remains a monolith concern (§13), since it requires business logic the gateway shouldn't own.

## 10. Scalability

- The monolith API is stateless (all session state in Redis/JWT, no in-process session storage) so it scales horizontally behind the gateway with no sticky-session requirement.
- WebSocket connections are the one stateful concern — handled via the Redis pub/sub decoupling in §4, so any API instance can serve any client's WebSocket regardless of which instance the job's orchestration worker happens to be running on.
- Orchestration workers (Celery) and sandboxed execution nodes (Document 12) scale independently of the API tier and of each other, matching their genuinely distinct load profiles (LLM-I/O-bound vs. CPU/GPU-execution-bound).

## 11. Event Bus

- Redis pub/sub suffices for v1's real-time streaming needs (§4); a heavier event bus (Kafka) is explicitly deferred until cross-service event patterns beyond "stream this job's updates to its connected clients" emerge (e.g., a future analytics pipeline consuming job-completion events at high volume) — introducing Kafka before that need is concrete would be premature infrastructure complexity for this stage.

## 12. Microservices vs. Modular Monolith — Service Boundaries & Dependency Graph

```
┌─────────────────────────────┐        ┌──────────────────────────┐
│   Monolith API (FastAPI)    │──────▶│  Orchestration Worker Pool │
│  Auth, Jobs, Billing,        │◀──────│  (Celery + LangGraph,      │
│  Integrations, Gallery       │  Redis │   Document 8)             │
└─────────────────────────────┘  pubsub└──────────────┬────────────┘
              │                                        │ dispatches
              │                                        ▼
              │                          ┌──────────────────────────┐
              │                          │ Sandboxed Execution Svc   │
              │                          │ (Document 12 isolation)   │
              │                          └──────────────────────────┘
              ▼
┌─────────────────────────────┐
│ Postgres / Qdrant / MinIO    │  (Document 10)
└─────────────────────────────┘
```

Dependency direction is strictly one-way where possible: the Orchestration Worker depends on the monolith only for reading initial job parameters and writing final results back (via direct DB access to the shared Postgres, not a synchronous API call, to avoid a hard runtime coupling that would make the monolith a single point of failure for long-running jobs already in flight).

## 13. Repository Structure

```
/apps
  /api          — FastAPI monolith (modules per §2, each with routers/services/models)
  /worker        — Celery + LangGraph orchestration (Document 8 agents live here)
  /sandbox-svc  — isolated execution service (Document 12)
/packages
  /shared-schemas — Pydantic models shared between api/worker (JobState, etc.) to avoid schema drift between the two runtime boundaries
/infra          — Terraform/Helm (Document 11)
```

## 14. Versioning

- API versioned via URL path (`/api/v1/`), with a deprecation-window policy (minimum 6 months' notice + parallel-run before removing a version) — appropriate given that FR-DEL/Document 14 explicitly supports third-party/CI programmatic integration, which is more version-sensitive than a purely first-party web client would be.

## 15. Monitoring & Logging

- Structured JSON logging throughout, correlated by `job_id`/`request_id`, shipped to the observability stack (Document 11: OpenTelemetry → Prometheus/Grafana).
- Application-level metrics: request latency/error rate per endpoint, queue depth per Celery queue, WebSocket connection count, cache hit rate (Finder search cache).

## 16. Rate Limiting

- **Gateway-level (§9):** coarse per-IP limits, pre-auth, protecting against basic abuse.
- **Application-level:** per-user/per-workspace, plan-tier-aware (FR-ACC-03's quota enforcement is a rate-limiting concern at the "jobs per period" granularity, distinct from the gateway's "requests per second" granularity) — implemented as a shared middleware/dependency in the monolith, reusing the same single-source-of-truth principle as RBAC (§7).

---
*End of Document 9. Proceeding next to Document 10: Database Architecture.*
