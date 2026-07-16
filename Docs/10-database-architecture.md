# PaperToProd — Document 10: Database Architecture

**Status:** Draft v1.0
**Primary store:** PostgreSQL (relational, transactional core). **Vector store:** Qdrant (embeddings for Finder similarity search + semantic cache). **Object store:** MinIO/S3-compatible (papers, generated repositories, logs).

---

## 1. Why This Split (rationale)

Postgres holds everything requiring transactional integrity and relational querying (accounts, jobs, billing, audit) — the vast majority of the schema. Qdrant is a purpose-built addition solely for the embedding-similarity workload (Document 8 Finder agent) that Postgres's `pgvector` extension *could* technically handle, but a dedicated vector engine gives materially better recall/latency at the scale expected once the paper corpus and cross-job cache grow, and decouples that workload's scaling profile from the core transactional database's. MinIO holds large binary/blob content (PDFs, generated repo archives, full logs) that has no business being row data in Postgres — keeping blobs out of the relational store keeps backup/restore and query performance of the core database predictable as usage grows.

## 2. Entity-Relationship Overview

```
users ──< workspace_members >── workspaces
                                    │
                                    │ 1:N
                                    ▼
                                  jobs ──1:1── job_artifacts (MinIO refs)
                                    │
                                    ├──1:N── job_state_checkpoints (LangGraph checkpoints)
                                    ├──1:N── job_events (audit_log entries, streamed to UI)
                                    └──1:1── fidelity_reports

workspaces ──1:N── api_keys
workspaces ──1:N── integrations (github_app_installs, byo_api_keys)
workspaces ──1:N── audit_log_entries (enterprise compliance log, distinct from job_events)
jobs ──N:1── users (submitter)
gallery_entries ──1:1── jobs (opt-in public share)
```

## 3. Core Schemas (representative DDL-level detail)

```sql
-- Identity & workspace
users(id PK, email UNIQUE, auth_provider, created_at, ...)
workspaces(id PK, name, plan_tier, created_at)
workspace_members(workspace_id FK, user_id FK, role ENUM('owner','admin','member','billing'), PRIMARY KEY(workspace_id, user_id))

-- Jobs (the central entity)
jobs(
  id PK, workspace_id FK, submitted_by FK(users),
  paper_source_url, paper_arxiv_id NULLABLE, paper_title, domain_classification,
  status ENUM('queued','running','awaiting_approval','complete','partial','failed','cancelled'),
  fidelity_score NUMERIC NULLABLE,
  compute_cost_cents, token_cost_cents,
  created_at, completed_at NULLABLE
)
job_state_checkpoints(id PK, job_id FK, node_name, state_snapshot JSONB, created_at)
  -- one row per LangGraph checkpoint (Document 8 §4); JSONB chosen over a fully normalized
  -- schema because JobState's shape evolves per-agent-version and per-paper-domain,
  -- and this table is written far more than it's ad hoc queried (it's read back
  -- sequentially for resume/audit, not filtered by arbitrary internal fields)
job_events(id PK, job_id FK, agent_name, event_type, payload JSONB, created_at)
  -- powers both the live-logs WebSocket stream (Document 9 §4) and post-hoc audit
job_artifacts(job_id FK, artifact_type ENUM('archive','dockerfile','readme','fidelity_report'), storage_key, created_at)
fidelity_reports(job_id PK/FK, coverage_pct, structural_check_pass_rate, execution_status, assumptions JSONB, license_disclosures JSONB)

-- Billing & integrations
api_keys(id PK, workspace_id FK, created_by FK(users), key_hash, scopes JSONB, last_used_at, revoked_at NULLABLE)
integrations(id PK, workspace_id FK, type ENUM('github_app','byo_llm_key'), encrypted_credential, installed_at)
audit_log_entries(id PK, workspace_id FK, actor_user_id FK, action, target, created_at)  -- append-only, enterprise compliance

-- Gallery
gallery_entries(job_id PK/FK, is_anonymous BOOL, shared_at)
```

## 4. Indexes

- `jobs(workspace_id, created_at DESC)` — primary access pattern for Job History/Dashboard (Document 3 §6), supports cursor pagination directly.
- `jobs(paper_arxiv_id)` — supports the "duplicate submission" check (Document 3 §2 edge case) and Finder's cross-job cache lookup.
- `job_events(job_id, created_at)` — sequential read pattern for both live-stream replay-on-reconnect and audit review.
- Partial index on `jobs(status) WHERE status IN ('queued','running','awaiting_approval')` — keeps the "active jobs" dashboard/ops query fast without scanning the full historical table as it grows.
- `audit_log_entries(workspace_id, created_at DESC)` — enterprise audit-log query pattern.

## 5. Storage (MinIO/object store layout)

```
/papers/{arxiv_id}/source.pdf
/jobs/{job_id}/repository.zip
/jobs/{job_id}/logs/full.log
/jobs/{job_id}/fidelity_report.md
```

Object keys are deliberately content-addressed by `arxiv_id` for the paper source (shared/reused across jobs referencing the same paper, avoiding redundant storage) but per-`job_id` for all generated artifacts (never shared, since two jobs on the same paper can diverge based on advanced-options overrides).

## 6. Lifecycle

- **Papers (`/papers/{arxiv_id}/`):** retained indefinitely (small, high-reuse-value, and central to the cross-job Finder cache).
- **Job artifacts:** retained per plan tier — free/trial tier 30 days, paid tiers indefinitely (or until explicit user deletion) — this policy lives in application logic (a scheduled cleanup job), not as a hard database constraint, since plan tier can change after a job is created.
- **`job_state_checkpoints`:** retained 30 days minimum (NFR-REL-03) regardless of plan tier, since these are essential for debugging/support even on free-tier failures, then eligible for compaction (keep only the final checkpoint per completed job, discard intermediate ones) to bound table growth.

## 7. Migration Strategy

- Standard versioned migrations (Alembic, given the FastAPI/Python stack) — additive-first discipline (new nullable columns before backfill, backfill before making NOT NULL, old-column removal only after a full deploy cycle confirms no code path reads it) to support zero-downtime deploys (Document 11/15).
- `job_state_checkpoints.state_snapshot`'s JSONB shape changes are handled via a schema-version field embedded in the JSON payload itself, not a table migration — since this column intentionally trades relational rigidity for flexibility (per §3's rationale), versioning happens at the application/Document-8-agent level.

## 8. Backup

- Postgres: continuous WAL archiving + daily full snapshots, cross-region replicated (Document 11), point-in-time-recovery window of 30 days.
- Qdrant: periodic snapshot backup (less critical — the similarity index is rebuildable from source data if needed, so its backup SLA is looser than Postgres's).
- MinIO: versioned bucket + cross-region replication for `job_artifacts` (paid-tier retained content) at minimum; papers corpus similarly replicated given its shared-reuse value.

## 9. Retention

Governed jointly by §6 (plan-tier lifecycle) and compliance requirements (Document 12 GDPR): a user-initiated account deletion triggers cascading anonymization (not necessarily hard deletion where a job is already part of the public Gallery, per Document 3 §11's stated policy) of `users`/`jobs.submitted_by`, while workspace-level billing/audit records required for legal/financial retention persist per applicable regulation.

## 10. Audit Tables

Two distinct audit surfaces, deliberately not merged (per Document 9 §8's rationale): `audit_log_entries` (account/workspace-level: who did what administratively) and `job_events` (agent-level: what the AI pipeline did on a specific job) — cross-referenced by `job_id`/`workspace_id` foreign keys for a compliance reviewer who needs both views (e.g., "who submitted this job, and what did the agents do with it").

## 11. Project History

`jobs` + `job_artifacts` + `fidelity_reports` together constitute a workspace's full project history (Document 3 §6's dashboard), queryable and exportable (CSV export of job metadata is a Should-priority future addition, not in the v1 FR list but a natural extension of this schema).

## 12. Artifacts

Covered in §5/§6 — `job_artifacts` table stores only metadata/pointers; actual bytes live in MinIO, keeping Postgres row sizes small and predictable regardless of generated-repository size.

## 13. Agent Logs

`job_events` (structured, queryable, powers live UI) + the full-fidelity `logs/full.log` object in MinIO (raw, for deep debugging/support) — the table is the queryable index into a subset of what the full object contains, not a duplicate of it.

## 14. Analytics

A nightly ETL (or, if volume justifies it later, a streaming pipeline) extracts anonymized/aggregated metrics from `jobs`/`job_events` into an analytics-optimized store (e.g., a columnar warehouse) for product metrics (Document 1 §11: reproduction success rate, fidelity score trends, repeat usage rate) — deliberately kept out of the transactional Postgres to avoid analytical queries competing with production job-serving load.

---
*End of Document 10. Proceeding next to Document 11: Infrastructure.*
