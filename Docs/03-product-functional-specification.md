# PaperToProd — Document 3: Product Functional Specification

**Status:** Draft v1.0
**Purpose:** Exhaustively describe every screen, workflow, user action, state, and failure mode so that frontend, backend, and QA can build/test against a single shared source of truth.

---

## 1. Screen Inventory

1. Landing / Marketing (unauthenticated)
2. Sign Up / Log In
3. Job Submission (the core entry point)
4. Job Progress (real-time agent execution view)
5. Job Results (validated artifact delivery)
6. Job Failure / Partial Result
7. Job History / Dashboard
8. Repository Explorer (browse generated code)
9. Fidelity Report View
10. Workspace Settings (org, billing, members)
11. Personal Settings (account, API keys, connected accounts)
12. Public Gallery (opt-in shared reproductions)
13. Shared Read-Only Job View (for links per FR-DEL-04)

---

## 2. Screen: Job Submission

**Purpose:** Get from "I have a paper" to "a job is running" in the fewest possible steps.

**Layout:** Single-focus centered input, large, with three input modes as tabs/toggle: arXiv URL, arXiv ID, PDF upload.

**Sections:**
- Primary input field (auto-detects URL vs. ID format as the user types/pastes).
- Optional advanced panel (collapsed by default): target framework override, "focus scope" hint (FR-ING-05), human-approval-checkpoint toggle (FR-RT-02), GitHub push destination.
- Recent/example papers carousel for first-time users (reduces blank-canvas hesitation, ties to NFR-UX-02's 60-second first-job goal).

**User actions:**
- Paste/type a URL → system validates format client-side immediately (does not wait for server round-trip to catch an obviously malformed URL).
- Upload a PDF → client-side file-type/size validation (max size stated explicitly, e.g. 25MB) before upload begins.
- Submit → transitions to Job Progress screen; underlying job is created via `POST /jobs` (Document 14).

**States:**
- Empty (default).
- Valid input detected (submit button enabled, subtle affirming micro-interaction — detailed in Document 5).
- Invalid input (inline error: "This doesn't look like a valid arXiv URL or ID").
- Uploading (progress indicator for large PDFs).
- Submitting (brief transitional state between click and navigation to Progress screen).

**Edge cases / failure states:**
- arXiv URL points to a withdrawn paper → system fetches metadata, detects withdrawal flag, blocks submission with explanation before a job is even created (avoids wasting a job/credit on unreproducible input).
- arXiv URL points to a paper with no methodology to implement (pure survey/position paper) → FR-ING-03: system performs a fast pre-check (lighter-weight than full extraction) and warns the user with an option to proceed anyway (some surveys do contain reproducible algorithms in appendices) or cancel.
- PDF upload is not text-extractable (pure scanned image with no OCR layer) → explicit error state directing the user to the arXiv/URL path instead, since OCR-quality methodology extraction is out of scope for v1 reliability guarantees.
- User is at/near plan quota → submission blocked pre-emptively with a clear quota message and upgrade path, not a failure after the job starts consuming resources.
- Duplicate submission (same paper already has a recent completed job for this user/workspace) → soft-prompt: "You already reproduced this on [date] — view that result, or run again?"

---

## 3. Screen: Job Progress

**Purpose:** Make a 5–20 minute wait feel transparent, trustworthy, and non-anxious — the user should always know what's happening and never wonder if the system is stuck.

**Layout:** A vertical or horizontal agent pipeline visualization (Extractor → Finder → Scaffolder → DevOps → Reviewer → Documentation Generator) with the active agent highlighted, plus a live log/terminal panel below (collapsible).

**User actions:**
- Watch passively (default).
- Expand live logs for detail.
- If a human-approval checkpoint is configured (FR-RT-02): approve/reject/modify the Finder agent's candidate-repository choice, or approve the Extractor's flagged assumptions, before the pipeline continues.
- Cancel job (with confirmation — cancelling mid-run still consumes partial usage per the metering model, which must be disclosed in the confirmation dialog).

**States:**
- Queued (job accepted, waiting for compute/agent availability — shows estimated wait).
- Running: Extracting.
- Running: Finding (may pause here awaiting human approval).
- Running: Generating.
- Running: Containerizing.
- Running: Validating (may loop — "Attempt 2 of 5" shown explicitly per FR-VAL-02, not hidden from the user).
- Running: Documenting.
- Awaiting human approval (blocking sub-state, timestamped, with a "resume automatically after 24h with defaults" fallback so a job never hangs forever on an absent user).
- Complete → auto-transitions to Job Results.
- Failed → transitions to Job Failure screen.
- Cancelled.

**Edge cases / failure states:**
- Agent step exceeds an expected time budget → UI shows a non-alarming "this is taking longer than usual" notice with an option to view detailed logs, rather than looking frozen.
- WebSocket connection drops → client falls back to polling `GET /jobs/{id}` and silently reconnects the socket, with no user-visible disruption beyond a small "reconnecting" indicator.
- Repair loop exhausts max retries → job transitions to a distinct "Partial Result" state (not a generic failure) if a prior attempt produced *something* usable, per NFR-FID-02's requirement to never overstate completeness while still delivering maximum value.

---

## 4. Screen: Job Results

**Purpose:** Deliver the artifact and, just as importantly, deliver *trust* in the artifact via the Fidelity Score and traceability.

**Sections:**
- Headline Fidelity Score with a one-line plain-language explanation of what it measures (never a bare unexplained number).
- Repository summary: file tree preview, key stats (LOC, test count, whether GPU is required).
- Primary actions: Download archive, Push to GitHub, Open Repository Explorer, View Fidelity Report.
- Assumptions/gaps panel (surfaces every flagged item from FR-EXT-02/03 — this is not buried in the README only; it's a first-class UI section).
- "What's next" suggestions (e.g., "Run the smoke test locally," link to generated README).

**States:** Fully validated / Partially validated (some components failed validation but others succeeded — explicitly labeled, per-component) / (Failed jobs do not reach this screen — see §5).

**Edge cases:**
- GitHub push fails (auth expired, target repo already exists and user didn't opt to overwrite) → inline retryable error, download-archive path remains available as a fallback so the user is never blocked from getting their artifact.

---

## 5. Screen: Job Failure / Partial Result

**Purpose:** Preserve trust even when the platform didn't fully succeed — never a dead end.

**Sections:**
- Clear, specific failure reason (not a generic "something went wrong") — e.g., "The generated training loop failed to run after 5 repair attempts. Last error: [specific trace excerpt]."
- Full logs, downloadable.
- Partial artifacts available for download if any component (e.g., scaffold + Extractor's methodology breakdown) completed even though final validation failed — the user should never get *nothing* if the system produced *something*.
- Clear path to retry (possibly with adjusted advanced options, e.g., a smaller compute ceiling or a different target framework) or to contact support with the job ID pre-filled.

---

## 6. Screen: Job History / Dashboard

**Purpose:** Support repeat usage (a key success metric from Document 1 §11).

**Sections:** Filterable/sortable list (by date, status, paper title, fidelity score); quick actions per row (re-run, download, share); usage/quota summary widget for the current billing period.

**Edge cases:** Very large history (1000+ jobs for a heavy team account) → requires server-side pagination and search, not client-side filtering of a full list (performance implication feeding Document 9's API design).

---

## 7. Screen: Repository Explorer

**Purpose:** Let a user inspect generated code without downloading, with the paper-traceability feature as the signature interaction.

**Sections:** File tree, code viewer with syntax highlighting, and — the differentiating feature — inline "paper reference" annotations that, on hover/click, show the exact paper excerpt (section + snippet, respecting copyright by paraphrase/summary rather than verbatim reproduction in the generated *documentation* layer, though the *paper's own equations/figures* as embedded reference images are permissible since they're the user's own uploaded/linked source material) a given code block implements.

**Edge cases:** Very large generated repositories → virtualized file tree and lazy-loaded file content, not a full-repo client-side load.

---

## 8. Screen: Fidelity Report

**Purpose:** The trust artifact, standalone and shareable independent of the code itself (useful for a PhD student citing this as a baseline, or a compliance reviewer auditing an enterprise job).

**Sections:** Coverage breakdown (which methodology components have corresponding code, which don't and why), structural check results, execution validation summary, full list of assumptions made with rationale, license/attribution disclosures for any reused code (FR-FIND-04).

---

## 9. Screen: Workspace Settings

**Sections:** Members list + role management (Owner/Admin/Member/Billing-only per FR-ACC-02), billing/plan/usage, connected integrations (GitHub App installation scope), audit log (enterprise tier), BYO-API-key configuration (FR-ACC-04).

**Edge cases:** Last Owner attempting to leave/downgrade their own role → blocked with explanation (a workspace must always retain at least one Owner).

## 10. Screen: Personal Settings

**Sections:** Profile, connected accounts (GitHub/Google OAuth), personal API keys (for programmatic job submission per Document 14), notification preferences (job-complete email/webhook).

## 11. Screen: Public Gallery

**Purpose:** GTM Phase 2 loop (Document 1 §10) — opt-in showcase of community reproductions.

**Sections:** Browsable/searchable gallery of publicly shared jobs, each showing paper title, fidelity score, and a link to the shared read-only Job View.

**Edge cases:** A user opts a job into the gallery, then later deletes their account → gallery entry policy must be decided explicitly (default: gallery entries persist as anonymized/orphaned public artifacts unless the user explicitly requests removal at account-deletion time — a decision that also has to satisfy Document 12's GDPR right-to-erasure requirements).

## 12. Screen: Shared Read-Only Job View

**Purpose:** Instructor-to-student and team-to-stakeholder sharing (FR-DEL-04).

**Sections:** Read-only version of Job Results + Fidelity Report; no access to Repository Explorer's live editing/download unless the sharer explicitly enabled artifact download on the share link; expirable link option.

---

## 13. Cross-Cutting States (apply across all screens)

- **Loading/skeleton states:** every data-dependent panel has a defined skeleton (detailed visually in Document 6).
- **Empty states:** first-time dashboard (no jobs yet) drives directly back to Job Submission with encouragement, not a bare empty table.
- **Offline/connectivity loss:** banner notice, read-only cached view of last-known state where feasible.
- **Session expiry mid-job:** job continues server-side regardless of client session (jobs are not tied to an active browser tab); user is prompted to re-authenticate but the job itself is never lost.

---
*End of Document 3. Proceeding next to Document 4: UX Strategy.*
