# PaperToProd — Document 15: Deployment Blueprint

**Status:** Draft v1.0

---

## 1. Environments

- **Development:** local (Docker Compose mirroring the production service topology at small scale — api/worker/sandbox-svc/postgres/redis/qdrant/minio) + ephemeral per-PR preview environments (spun up in a lightweight shared dev cluster) for reviewing frontend/API changes without a full staging deploy.
- **Staging:** full production-topology replica (same Helm charts, Document 11 §3, smaller node counts), running against a synthetic/anonymized dataset and a reduced Golden Dataset subset for pre-release validation — never touches real customer data.
- **Production:** as specified in Document 11, multi-AZ, with the standby DR region (Document 11 §8) kept warm but not serving live traffic under normal operation.

## 2. CI/CD Pipeline (elaborating Document 11 §5)

```
PR opened → lint/typecheck/unit tests → preview environment deploy
           → integration tests (against preview env)
           → [if agent/prompt files touched] Golden Dataset regression eval
Merge to main → build+tag images → deploy to staging (auto)
             → smoke test suite (Document 13 §10) against staging
             → [manual approval gate] → deploy to production
Production deploy → blue-green cutover (§3) → post-deploy smoke suite → monitor error-rate/latency window (15 min) before fully retiring the old version
```

## 3. Release Strategy

- **API/monolith service:** blue-green deployment — new version deployed alongside old, smoke-tested against production-adjacent traffic mirroring before the load balancer cuts over, enabling instant rollback (flip back to "blue") if the post-cutover monitoring window (above) shows regression.
- **Orchestration Worker:** canary deployment rather than blue-green — a small percentage of new jobs route to the new worker version first (since worker behavior changes, especially agent prompt/graph changes, are exactly the class of change most likely to have subtle quality regressions the Golden Dataset gate didn't catch), with the canary percentage ramped up over hours, not minutes, specifically because a single job's outcome takes 5–20 minutes to observe (Document 2 NFR-PERF-02) — a canary window shorter than that would not actually observe enough real outcomes to be meaningful.
- **Sandboxed Execution Service:** blue-green, given its stateless-per-job nature (Document 12 §6) makes instant cutover safe with no in-flight-job continuity concern (in-flight validations simply complete on whichever version they started on).

## 4. Rollback

- Blue-green services: instant traffic-flip rollback (no redeploy needed, the old version is still warm during the monitoring window).
- Canary (Worker): halt canary ramp-up and route 100% of new jobs back to the stable version; in-flight jobs already routed to the canary version continue on it (LangGraph checkpointing, Document 8 §4, means a mid-flight job isn't corrupted by the canary being "rolled back" around it — it simply finishes on the version it started on).
- Database migrations: strictly additive-first (Document 10 §7) specifically so that a code rollback never requires a corresponding destructive schema rollback — the previous code version remains compatible with the new (additive) schema.

## 5. Observability in Deployment

- Every deploy is tagged/correlated in the OpenTelemetry/Grafana stack (Document 11 §7) so the post-deploy monitoring window's dashboards are automatically scoped to "since this deploy," not requiring a human to manually filter by timestamp during an incident.

## 6. Runbooks

Maintained as living documents (outside this architecture spec, but their required contents are specified here) for: GPU-pool saturation response, repair-loop-exhaustion-rate spike investigation (tracing back to Document 13 §7's chaos-engineering-validated failure modes), LLM-provider outage confirmation and manual fallback-chain verification (Document 8 §6), sandbox-service security-incident containment (isolate the affected node, preserve logs, do not simply restart-and-forget given the elevated-risk nature of that service per Document 12 §6), and database failover verification.

## 7. Incident Response

- Severity-tiered (SEV1: production down or a security-relevant sandbox escape suspected → immediate all-hands page; SEV2: degraded performance or elevated repair-loop-exhaustion rate → on-call engineer response within a defined SLA; SEV3: non-urgent quality regression flagged by Golden Dataset trend, Document 13 §12 → next-business-day triage).
- **Security-specific escalation path:** any suspected sandbox-isolation breach (Document 12 §6) triggers a distinct, stricter runbook than a standard SEV1 — includes immediate isolation of the affected sandbox node from the network (not just the cluster) pending forensic review, given the elevated trust boundary that component represents.

---
*End of Document 15. Proceeding next to Document 16: Engineering Roadmap.*
