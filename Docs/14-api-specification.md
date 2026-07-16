# PaperToProd — Document 14: API Specification

**Status:** Draft v1.0
**Base URL:** `https://api.papertoprod.com/api/v1`
**Auth:** Bearer token (session JWT for web client, or API key for programmatic access, Document 9 §7). All endpoints below require auth unless marked public. Full machine-readable contract lives in the generated OpenAPI 3.1 spec (`/openapi.json`, FastAPI-native) — this document is the human-readable companion, not a duplicate source of truth.

---

## 1. Jobs

### `POST /jobs`
Create a new job (FR-ING-01).

**Request:**
```json
{
  "source": { "type": "arxiv_url" | "arxiv_id" | "pdf_upload", "value": "string (URL/ID) or upload_token" },
  "options": {
    "target_framework": "pytorch" | "jax" | "tensorflow" | null,
    "focus_scope": "string | null",
    "require_human_approval": "boolean, default false",
    "github_push_destination": "string (repo full_name) | null"
  }
}
```

**Response `201`:**
```json
{ "job_id": "uuid", "status": "queued", "created_at": "iso8601" }
```

**Errors:**
- `400` — malformed source (invalid URL/ID format).
- `409` — duplicate submission detected (includes `existing_job_id` in body per Document 3 §2 edge case).
- `422` — pre-flight check failed (withdrawn paper, non-extractable PDF, no methodology detected) — includes `reason` field with a specific machine-readable code (`withdrawn_paper`, `unreproducible_content`, `pdf_not_extractable`) plus human-readable `message`.
- `429` — quota exceeded (includes `quota_reset_at`, `upgrade_url`).

### `GET /jobs/{job_id}`
Full current `JobState` snapshot (Document 8 §2), used both for direct polling and as the WebSocket-reconnect fallback (Document 9 §4).

**Response `200`:** full job object including `status`, `fidelity_score` (null until computed), `per_component_status[]`, `assumptions[]`, `artifacts` (download links, present once `status` is `complete` or `partial`).

**Errors:** `404` (not found or not authorized), `403` (belongs to a different workspace).

### `GET /jobs`
List jobs for the current workspace (Document 3 §6 dashboard).

**Query params:** `status`, `date_from`, `date_to`, `search` (title match), `cursor`, `limit` (default 20, max 100).

**Response `200`:** `{ "jobs": [...], "next_cursor": "string | null" }` — cursor-based per Document 9 §3's stability rationale.

### `POST /jobs/{job_id}/cancel`
Cancel a running job (Document 3 §3).

**Response `200`:** `{ "status": "cancelled" }`. **Errors:** `409` if job already reached a terminal state.

### `POST /jobs/{job_id}/approve`
Resolve a pending human-approval checkpoint (FR-RT-02).

**Request:** `{ "checkpoint": "finder_candidate_selection" | "extractor_gap_review", "decision": "approve" | "choose_alternative" | "skip", "selection": "candidate_repo_url | null" }`

**Response `200`:** job resumes; **Errors:** `409` if no checkpoint is currently pending, `410` if the 24-hour auto-continue window already elapsed and a default decision was applied.

### `GET /jobs/{job_id}/logs`
Full log stream (non-realtime fetch — for the Job Failure screen's expanded-by-default log view, Document 6).

**Query params:** `since_sequence` (for incremental fetch), `format` (`json` | `text`).

## 2. Job Artifacts

### `GET /jobs/{job_id}/artifacts/repository`
Returns a signed, time-limited download URL for the repository archive.

### `POST /jobs/{job_id}/artifacts/push-to-github`
**Request:** `{ "destination_repo": "string", "create_new": "boolean" }`
**Response `200`:** `{ "repo_url": "string" }`. **Errors:** `401` (GitHub auth expired — response includes `reauth_url`), `409` (target repo exists and `create_new` conflict per Document 3 §4 edge case).

### `GET /jobs/{job_id}/fidelity-report`
Returns the structured Fidelity Report (Document 6's Fidelity Report page data source).

## 3. Workspaces & Members

### `GET /workspaces/{workspace_id}` / `PATCH /workspaces/{workspace_id}`
Standard workspace metadata read/update (name, plan tier is read-only here — changed via Billing endpoints).

### `GET /workspaces/{workspace_id}/members` / `POST .../members` (invite) / `PATCH .../members/{user_id}` (role change) / `DELETE .../members/{user_id}`
RBAC-gated per Document 9 §7; `DELETE`/role-downgrade on the last remaining Owner returns `409` (Document 3 §9 edge case).

## 4. Integrations

### `POST /workspaces/{workspace_id}/integrations/github-app/install`
Initiates GitHub App OAuth install flow, returns install URL.

### `POST /workspaces/{workspace_id}/integrations/byo-key` (enterprise-gated)
**Request:** `{ "provider": "openai" | "anthropic", "api_key": "string" }` — stored per Document 12 §7's envelope encryption; response never echoes the key back.

## 5. API Keys

### `POST /workspaces/{workspace_id}/api-keys`
**Request:** `{ "name": "string", "scopes": ["jobs:create", "jobs:read"] }`
**Response `201`:** `{ "key": "string (shown once)", "key_id": "uuid" }` — the only time the raw key is ever returned, consistent with standard API-key issuance practice.

### `DELETE /workspaces/{workspace_id}/api-keys/{key_id}`
Revokes immediately (Document 9 §7's per-request scope re-check means this takes effect on the very next call, not after a cache TTL).

## 6. Billing

### `GET /workspaces/{workspace_id}/usage`
Current-period usage summary (jobs run, compute/token cost, quota remaining) — powers Document 6's `UsageSummaryWidget`.

### `POST /workspaces/{workspace_id}/billing/checkout-session`
Creates a payment-provider checkout session for plan upgrade (delegates actual payment UI to the provider, e.g., Stripe Checkout).

## 7. Gallery

### `POST /jobs/{job_id}/gallery` (opt-in share)
**Request:** `{ "anonymous": "boolean" }`

### `GET /gallery` (public, no auth required)
**Query params:** `domain`, `sort` (`score` | `recent`), `cursor`.

### `DELETE /jobs/{job_id}/gallery`
Removes from gallery (does not delete the underlying job).

## 8. Shared Links

### `POST /jobs/{job_id}/share-link`
**Request:** `{ "expires_in_days": "number | null", "allow_download": "boolean" }`
**Response `201`:** `{ "share_url": "string", "token": "string" }`

### `GET /shared/{token}` (public, no auth required)
Read-only job view data (Document 6's Shared Read-Only Job View), respecting `allow_download` and expiry.

## 9. WebSocket

### `WS /ws/jobs/{job_id}`
Auth via query-param token (short-lived, issued by `GET /jobs/{job_id}/ws-token` since browsers can't set auth headers on WebSocket upgrade requests). Streams `JobState` delta events:

```json
{ "type": "agent_transition", "agent": "finder", "status": "active", "sequence": 42 }
{ "type": "log_line", "agent": "scaffolder", "line": "string", "sequence": 43 }
{ "type": "approval_required", "checkpoint": "finder_candidate_selection", "candidates": [...] }
{ "type": "job_complete", "fidelity_score": 87.2 }
```

Each event carries a monotonic `sequence` number so a reconnecting client can request replay-since (`GET /jobs/{job_id}/events?since_sequence=N`) and never miss an event across a brief disconnect (Document 3 §3 edge case).

## 10. Pagination

Cursor-based (`cursor`/`next_cursor`) on all list endpoints per Document 9 §3 — opaque cursor tokens, not raw offsets, so results remain stable under concurrent inserts.

## 11. Streaming

Beyond the WebSocket (real-time), `GET /jobs/{job_id}/logs` supports `Accept: text/event-stream` (SSE) as a simpler alternative for programmatic/CI integrations that don't need bidirectional WebSocket semantics (e.g., a CI pipeline polling job status doesn't need the approval-response channel, only the one-way event stream).

## 12. OpenAPI

Full spec auto-generated from FastAPI route definitions (`/openapi.json`), including all request/response Pydantic models shared with the `packages/shared-schemas` module (Document 9 §13) — guarantees the published spec can never drift from actual server behavior, since both are generated from the same source models.

---
*End of Document 14. Proceeding next to Document 15: Deployment Blueprint.*
