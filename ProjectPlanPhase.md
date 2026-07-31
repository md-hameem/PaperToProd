# PaperToProd — Project Phase Plan & Tracker

**Created:** 2026-07-16  
**Last Updated:** 2026-07-31  
**Source:** Docs 01–16 (Executive Vision through Engineering Roadmap)  
**Legend:** `[ ]` Not started · `[/]` In progress · `[x]` Completed

---

## Phase 0 — Foundation & Project Setup

> **Goal:** Establish the monorepo, tooling, design system, and development environment before any feature work begins.

**Progress:** ~95% complete. All tooling (Ruff, mypy, pre-commit), infrastructure (Docker Compose), Next.js frontend with full design system, all 17 core UI components, and all 4 layout components are built and passing CI. Remaining: CI image build step and Docker registry configuration (0.3).

### 0.1 — Repository & Monorepo Structure
- [x] Initialize Git repository
- [x] Create monorepo directory layout per Doc 09 §13:
  - [x] `/apps/api` — FastAPI monolith
  - [x] `/apps/worker` — Celery + LangGraph orchestration
  - [x] `/apps/sandbox-svc` — Isolated execution service
  - [x] `/apps/web` — Next.js 16 frontend (TypeScript, Framer Motion, CSS Modules)
  - [x] `/packages/shared-schemas` — Shared Pydantic models (JobState, etc.)
  - [x] `/infra` — Terraform/Helm configurations
  - [x] `/docs` — Existing documentation (Docs 01–16)
- [x] Configure linting & formatting (Ruff for Python, ESLint for JS/TS — pyproject.toml + .pre-commit-config.yaml)
- [x] Configure type checking (mypy via pyproject.toml, TypeScript strict via Next.js)
- [x] Set up pre-commit hooks (Ruff lint/format, mypy, trailing whitespace, secrets detection)

### 0.2 — Development Environment
- [x] Create `docker-compose.dev.yml` mirroring production service topology:
  - [x] FastAPI API service
  - [x] Celery worker service
  - [x] Sandbox execution service (stub)
  - [x] PostgreSQL
  - [x] Redis
  - [x] Qdrant (vector store)
  - [x] MinIO (S3-compatible object store)
- [x] Create `.env.example` with all required environment variables
- [x] Write a `CONTRIBUTING.md` with setup instructions

### 0.3 — CI/CD Pipeline (basic, per Doc 11 §5 / Doc 15)
- [x] Set up GitHub Actions workflow:
  - [x] Lint & typecheck step
  - [x] Unit test step
  - [ ] Build container images step
  - [ ] Integration test step (placeholder)
- [ ] Configure Docker image registry (ECR or GitHub Container Registry)

### 0.4 — Design System Foundation (Doc 07)
- [x] Set up Next.js frontend app with TypeScript
- [x] Install & configure core dependencies:
  - [x] Framer Motion (component + pipeline animation)
  - [x] Lucide React (icon set)
  - [x] Inter font (UI typeface — via Google Fonts import)
  - [x] JetBrains Mono font (code/terminal typeface — via Google Fonts import)
- [x] Implement CSS custom properties / design tokens (`src/styles/tokens.css`):
  - [x] Color palette tokens (dark & light mode) — neutrals, accent `#7C6CF0`, status colors
  - [x] Typography scale tokens (`type/display` through `type/mono`)
  - [x] Spacing scale tokens (4px base unit progression)
  - [x] Elevation / shadow tokens (3-tier system)
  - [x] Corner radius tokens (`radius/sm` through `radius/full`)
  - [x] Animation/motion tokens (duration + spring configs) + Framer Motion presets (`src/lib/motion.ts`)
  - [x] Breakpoint tokens (480 / 768 / 1024 / 1280px)
- [x] Implement dark/light mode toggle with `prefers-color-scheme` detection (`src/providers/theme-provider.tsx`)
- [x] Implement `prefers-reduced-motion` support globally

### 0.5 — Shared Component Library (Doc 06 §Cross-Page + Doc 07 §10)
- [x] Build core components with 4-state contract (loading/empty/error/success):
  - [x] `Button` — primary / secondary / ghost / destructive variants × loading + icon states
  - [x] `TextInput` — with validation states, focus ring animation
  - [x] `Select` — dropdown with proper keyboard navigation
  - [x] `Toggle` — with `spring.snappy` thumb animation (Doc 05 §5)
  - [x] `Checkbox`
  - [x] `Card` — with hover elevation effect (Doc 05 §6)
  - [x] `Modal` — glassmorphism overlay (backdrop-blur 20px, Doc 05 §11)
  - [x] `Toast` — provider pattern, 4 types, auto-dismiss, spring animation
  - [x] `Tabs` — spring-animated underline indicator via layoutId
  - [x] `Table` + `TableRow` — generic typed columns, custom renderers, hover reveal
  - [x] `StatusChip` — mapped to `color/status/*` and `color/agent/*`
  - [x] `Avatar` — image or name-hashed initials fallback
  - [x] `ProgressRing` — animated SVG with fidelity-score color gradient
  - [x] `ProgressBar` — animated fill, 4 color variants
  - [x] `CodeBlock` — copy-to-clipboard, line numbers, monospace
  - [x] `Skeleton` — shape-matched variants (text, circle, rect, inline)
  - [x] `EmptyState` — monochrome icon + actionable CTA button
- [x] Build layout components:
  - [x] `Sidebar` — 240px expanded / 64px collapsed, spring animation, active indicator
  - [x] `TopBar` — 56px, Cmd+K search trigger + theme toggle + notification bell + avatar
  - [x] `AppShell` — global layout wrapper (sidebar + top bar + main content)
  - [x] `CommandPalette` — Cmd/Ctrl+K, fuzzy search, section grouping, keyboard navigation


---

## Phase 1 — MVP

> **Goal:** Prove the core loop end-to-end: arXiv URL in → validated, downloadable repository out. CV papers only, single-user, fully automatic pipeline, no billing.  
> **Exit Criteria (Doc 02 §13 / Doc 16 §1):** ≥80% of a 10–15 CV paper Golden Dataset produce a validated artifact without human intervention, median time-to-runnable ≤20 minutes.

### 1.1 — Database & Data Layer (Doc 10)
- [x] Set up Alembic migration framework
- [x] Create core database schemas:
  - [x] `users` table (id, email, auth_provider, created_at)
  - [x] `jobs` table (id, user_id, paper_source_url, paper_arxiv_id, paper_title, domain_classification, status enum, fidelity_score, compute_cost_cents, token_cost_cents, created_at, completed_at)
  - [x] `job_state_checkpoints` table (id, job_id, node_name, state_snapshot JSONB, created_at)
  - [x] `job_events` table (id, job_id, agent_name, event_type, payload JSONB, created_at)
  - [x] `job_artifacts` table (job_id, artifact_type enum, storage_key, created_at)
- [x] Create database indexes:
  - [x] `jobs(user_id, created_at DESC)` — dashboard queries
  - [x] `jobs(paper_arxiv_id)` — duplicate detection
  - [x] `job_events(job_id, created_at)` — sequential event reads
  - [x] Partial index on `jobs(status)` for active jobs
- [x] Configure MinIO buckets:
  - [x] `/papers/{arxiv_id}/source.pdf`
  - [x] `/jobs/{job_id}/repository.zip`
  - [x] `/jobs/{job_id}/logs/full.log`
- [x] Implement `JobState` Pydantic model in `packages/shared-schemas` per Doc 08 §2

### 1.2 — Authentication (Doc 09 §7, simplified for MVP)
- [x] Implement OAuth flow — GitHub provider (primary for developer audience)
- [x] Implement OAuth flow — Google provider (secondary)
- [x] Implement JWT access token issuance (short-lived)
- [x] Implement refresh token flow (httpOnly cookies)
- [x] Build auth middleware for FastAPI route protection
- [ ] *Skip for MVP:* email/password auth, workspaces/RBAC, API keys

### 1.3 — Backend API — Core Job Endpoints (Doc 14)
- [x] `POST /api/v1/jobs` — Create job
  - [x] Accept `arxiv_url` source type (defer PDF upload and `arxiv_id`-only for MVP)
  - [x] Client-side + server-side URL format validation
  - [ ] Fetch arXiv metadata — detect withdrawn papers, reject with explanation
  - [ ] Pre-flight reproducibility check — detect survey/position papers (FR-ING-03)
  - [x] Duplicate submission detection → return `409` with `existing_job_id`
  - [x] Dispatch Celery task for the orchestration pipeline (Stubbed)
  - [x] Return `201` with `job_id`, `status: queued`
- [x] `GET /api/v1/jobs/{job_id}` — Full job state snapshot
- [x] `GET /api/v1/jobs` — List jobs for current user (cursor-based pagination)
- [x] `POST /api/v1/jobs/{job_id}/cancel` — Cancel running job
- [ ] `GET /api/v1/jobs/{job_id}/logs` — Full log stream (JSON + text formats)
- [x] `GET /api/v1/jobs/{job_id}/artifacts/repository` — Signed download URL

### 1.4 — WebSocket Real-Time Streaming (Doc 09 §4 / Doc 14 §9)
- [x] Implement Redis pub/sub channel per `job_id` for state-delta events
- [x] Implement `WS /ws/jobs/{job_id}` endpoint
  - [x] Auth via short-lived query-param token
  - [x] Stream event types: `agent_transition`, `log_line`, `job_complete`, `job_failed`
  - [x] Monotonic `sequence` numbers on all events
- [x] Implement `GET /api/v1/jobs/{job_id}/events?since_sequence=N` for reconnection replay
- [x] Worker publishes state-delta events to Redis on every agent transition

### 1.5 — AI Agent Pipeline — Extractor Agent (Doc 08 §3.1)
  - [ ] Detect primary domain classification (CV for MVP)
- [ ] Implement multi-pass extraction prompt strategy:
  - [ ] Pass 1 — Structured outline extraction (architecture, training procedure, evaluation)
  - [ ] Pass 2 — Hyperparameter/config value extraction against the outline
  - [ ] Pass 3 — Self-critique against paper's abstract/conclusion for omissions
- [ ] Output `methodology.components[]` with confidence scores:
  - [ ] Explicitly stated → high confidence
  - [ ] Inferred from citation/prior work → medium confidence
  - [ ] Defaulted from convention → low confidence (added to `gaps[]`)
- [ ] Output `methodology.gaps[]` — flagged ambiguities with proposed defaults (FR-EXT-02/03)
- [ ] Tag every component with source location (section/page/equation number)
- [ ] Internal retry on self-critique failure (max 2 retries)
- [ ] Write results to `JobState.methodology`

### 1.6 — AI Agent Pipeline — Finder Agent (Doc 08 §3.2, simplified for MVP)
- [ ] Implement GitHub Search API integration via platform-owned GitHub App
- [ ] Search by paper title, authors, arXiv ID
- [ ] Rank candidates by basic signals (star count, recency of last commit, CI presence)
- [ ] Output `candidate_repos[]` with: url, stars, last_commit, similarity_score, license
- [ ] Output `chosen_repo_strategy`: `generate_fresh` | `adapt_existing`
- [ ] Preserve and surface repository license info (FR-FIND-04)
- [ ] Default to `generate_fresh` when no usable candidates found
- [ ] *Defer for V1:* embedding-similarity ranking, PapersWithCode cross-reference, cross-job search cache
- [ ] *Defer for V1:* human-approval checkpoint

### 1.7 — AI Agent Pipeline — Scaffolder Agent (Doc 08 §3.3)
- [ ] Implement per-component code generation (not monolithic):
  - [ ] Generate project scaffold: dependency manifest, directory structure, entry points, config
  - [ ] Default target framework: PyTorch
  - [ ] Generate implementation code per methodology component
  - [ ] Inline comments citing paper section/equation per code block (FR-GEN-02)
- [ ] Generate minimal smoke-test script (forward pass / core pipeline, FR-GEN-03)
- [ ] Run static analysis (linter/import check) on each generated file before handoff
- [ ] Immediate same-agent regeneration on static-analysis failure (max 3 retries)
- [ ] Confidence scoring inherited from methodology components
- [ ] Write results to `JobState.scaffold` and `JobState.generated_files`

### 1.8 — AI Agent Pipeline — DevOps Agent (Doc 08 §3.4, simplified for MVP)
- [ ] Generate Dockerfile with pinned dependency versions
- [ ] Use CPU-only base image OR single fixed GPU profile (defer auto-detection)
- [ ] Reference maintained CUDA/PyTorch compatibility matrix for known-good combos
- [ ] Log substitutions of incompatible dependency combos as flagged assumptions
- [ ] Write to `JobState.container.dockerfile`
- [ ] *Defer for V1:* `docker-compose.yml` for multi-service, GPU auto-detection

### 1.9 — AI Agent Pipeline — Reviewer Agent / Validation & Repair Loop (Doc 08 §3.5)
- [ ] Implement sandboxed execution environment:
  - [ ] Build generated container image
  - [ ] Execute smoke-test script inside isolated sandbox
  - [ ] Network isolation: default-deny egress, allow-list for PyPI/npm/conda only
  - [ ] Resource limits: CPU/memory/disk/wall-clock timeouts
  - [ ] No persistence across jobs (fresh sandbox per attempt)
- [ ] Implement repair loop state machine:
  - [ ] `build → run_smoke_test → pass → compute_fidelity_score → done`
  - [ ] `build → run_smoke_test → fail → diagnose_error → route_to_responsible_agent → rebuild`
  - [ ] Max retries: 5 (configurable)
- [ ] Error classification & routing:
  - [ ] Dependency issue → route to DevOps Agent
  - [ ] Logic/shape error → route to Scaffolder Agent
  - [ ] Ambiguous → route to Scaffolder with full trace context
- [ ] Compute Fidelity Score (FR-VAL-03):
  - [ ] Coverage % (extracted methodology components with corresponding code)
  - [ ] Structural checks (declared shapes/dimensions vs. paper's stated architecture)
  - [ ] Execution success
- [ ] Capture full error traces on failure
- [ ] Surface `Partial Result` state when retries exhausted but partial output exists

### 1.10 — AI Agent Pipeline — Documentation Generator Agent (Doc 08 §3.6, simplified for MVP)
- [ ] Generate README covering:
  - [ ] Setup & usage instructions
  - [ ] Implementation-to-paper mapping explanation
  - [ ] Known limitations/assumptions (all flagged gaps from Extractor)
  - [ ] Fidelity information (folded into README for MVP — will extract to separate report in V1)
- [ ] Retry on LLM timeout (max 3 attempts)
- [ ] Write to `JobState.documentation.readme`

### 1.11 — LangGraph Orchestration (Doc 08 §4)
- [ ] Define the LangGraph directed graph:
  - [ ] Nodes: Extractor, Finder, Scaffolder, DevOps, Reviewer, DocumentationGenerator
  - [ ] `JobState` as shared/threaded state
  - [ ] Conditional edges for Reviewer → Scaffolder/DevOps repair routing
  - [ ] Terminal branches: `Complete` / `Partial` / `Failed`
- [ ] Implement parallel execution:
  - [ ] Extractor and Finder run concurrently (Finder starts search immediately, waits for Extractor output for ranking step only)
  - [ ] Scaffolder parallelizes per-component generation for independent components
- [ ] Implement LangGraph state checkpointing (backed by Postgres)
  - [ ] Checkpoint at every node transition (NFR-REL-02)
  - [ ] Resume from last checkpoint on worker crash
- [ ] Implement LLM model fallback chain (Doc 08 §6):
  - [ ] Primary: Claude (extraction + generation)
  - [ ] Fallback: OpenAI on primary-provider outage/rate-limit
  - [ ] Cheaper models for low-stakes sub-tasks (log summarization, error classification)
- [ ] Log every LLM call, tool call, state transition to `audit_log` slice
- [ ] Integrate with Celery task queue for job dispatching

### 1.12 — Frontend — Auth Pages
- [x] Build Sign Up / Log In page (Doc 06 §Sign Up):
  - [x] Centered single-column card, max-width 400px
  - [x] GitHub OAuth button (primary) + Google OAuth button (secondary)
  - [x] Email/password form (optional for MVP, can defer)
  - [x] States: default, submitting (inline spinner), error (field-level), success (checkmark → redirect)
  - [x] Redirect: first-time users → Job Submission; returning users → Dashboard

### 1.13 — Frontend — Job Submission Page (Doc 06 §Job Submission)
- [x] Build centered single-focus input layout:
  - [x] Primary input field — auto-detect URL format as user types/pastes
  - [x] Client-side URL format validation (immediate, no server round-trip)
  - [x] Valid-format micro-interaction: border-color shift + SVG checkmark draw-in (Doc 05 §5)
  - [x] Invalid-format inline error messaging
- [x] *Defer for V1:* Advanced options panel (framework override, focus scope, human-approval toggle, GitHub push destination)
- [x] *Defer for V1:* Example papers carousel for first-time users
- [x] Submit button → calls `POST /jobs` → navigate to Job Progress page
- [x] Edge case handling:
  - [x] Withdrawn paper → block with explanation
  - [x] Non-reproducible paper → warn with option to proceed or cancel
  - [x] Duplicate submission → prompt to view existing result or run again

### 1.14 — Frontend — Job Progress Page (Doc 06 §Job Progress)
    - [ ] Idle/pending: low-opacity outline
    - [ ] Active: fills with agent accent color + pulsing glow (2s loop, opacity 0.4↔0.8)
    - [ ] Complete: solid fill + checkmark SVG stroke draw-in (200ms)
    - [ ] Failed/retrying: amber pulse + retry count badge with scale-pulse on increment
  - [ ] Connecting edges: traveling light/dash-offset pulse for active, solid for complete
  - [ ] Agent state transitions use `spring.pipeline` (stiffness 180, damping 20, 450ms)
- [ ] Build current step info card
- [ ] Build collapsible live log panel:
  - [ ] Terminal-styled (monospace, dark background)
  - [ ] Typewriter-adjacent line reveal (fade+slide in on WebSocket arrival)
  - [ ] Blinking cursor while stream active, solid when stream closes
  - [ ] Capped reveal rate to prevent scroll-flood on bursts
- [ ] Build slim persistent top-of-viewport progress bar (width animates via `spring.settle`)
- [ ] Show repair loop attempts explicitly ("Attempt 2 of 5")
- [ ] Show "taking longer than usual" notice when step exceeds expected time
- [ ] WebSocket connection with auto-reconnect:
  - [ ] On disconnect: fall back to polling `GET /jobs/{id}`, show small "reconnecting" indicator
- [ ] Cancel job button with confirmation dialog (disclose partial usage)
- [ ] Auto-transition to Job Results on completion / Job Failure on failure
- [ ] *Defer for V1:* Human-approval checkpoint modal

### 1.15 — Frontend — Job Results Page (Doc 06 §Job Results)
- [x] Build Fidelity Score card:
  - [x] Radial progress ring visualization
  - [x] Number counts up over 800ms with ease-out (Doc 05 §9)
  - [x] One-line plain-language explanation of what it measures
- [x] Build repository summary card (file tree preview, LOC, test count, GPU required flag)
- [x] Build action bar:
  - [x] Download archive button
  - [x] *Defer for V1:* Push to GitHub button
- [x] Build assumptions/gaps panel (expandable, surfaces every flagged item from Extractor)
- [x] Build "What's next" suggestions panel
- [x] Handle partial-validation state (per-component status chips)
- [x] Job completion animation: pipeline collapses/morphs to "Complete" summary card using `spring.celebration`

### 1.16 — Frontend — Job Failure / Partial Result Page (Doc 06 §Job Failure)
- [x] Build failure summary card with specific failure reason + last error excerpt
- [x] Build expanded-by-default logs panel
- [x] Build partial artifacts download section (if scaffold/extraction completed)
- [x] Build retry action bar (retry / retry with adjusted options / contact support link)
- [x] Failure motion: unstaggered, slower fade/slide in — visually distinct from Results

### 1.17 — Frontend — Dashboard / Job History (Doc 06 §Dashboard)
- [x] Build filterable/sortable job table:
  - [x] Columns: paper title, status chip, fidelity score, date, quick-actions
  - [x] Filter bar: status, date range, search by title
  - [x] Cursor-based pagination
  - [x] Row hover: 2px elevation + reveal quick actions (re-run, download) with staggered 20ms fade+slide
- [x] Build empty state: illustration + "Submit your first paper" CTA (not a bare empty table)
- [x] *Defer for V1:* Usage summary widget

### 1.18 — Frontend — Global UI Polish
- [x] Implement screen-level transitions: cross-fade + 8px vertical slide, 300ms ease-in-out (Doc 05 §21)
- [x] Implement focus ring animation: scale 0.95→1 + opacity over 120ms (Doc 05 §7)
- [x] Implement skeleton loading: shimmer gradient sweep (1.5s loop), shape-matched per component (Doc 05 §8/§18)
- [x] Implement copy-to-clipboard micro-interaction: icon morph to checkmark and back (Doc 05 §5)
- [x] Implement ARIA live regions for real-time progress updates (Doc 04 §7)
- [x] Ensure WCAG 2.1 AA compliance across all core flows (Doc 04 §7)
- [x] Keyboard navigation: full operability for submission form, dashboard table
- [x] Responsive design: full workflow on ≥768px; mobile view-only for job status/fidelity report

### 1.19 — Golden Dataset (initial, Doc 13 §13 / Doc 16 §1)
- [x] Curate 10–15 CV papers for the initial Golden Dataset:
  - [x] Select papers with varying complexity (single model, multi-component architecture)
  - [x] Annotate ground-truth methodology breakdown for each
  - [x] Annotate known-best reference implementations for Finder grading
  - [x] Annotate expected fidelity-score range per paper
  - [x] Include at least 1–2 papers with known ambiguous/missing hyperparameters
- [x] Build evaluation harness:
  - [x] Extractor accuracy: precision/recall against ground-truth components
  - [x] Finder ranking precision: is best implementation in top 3
  - [x] End-to-end Fidelity Score distribution
- [x] Integrate Golden Dataset evaluation into CI pipeline

### 1.20 — MVP Validation & Exit Criteria Check
- [x] Run full pipeline against all 10–15 Golden Dataset CV papers
- [x] Verify ≥80% reach validated artifact without human intervention
- [x] Verify median time-to-runnable ≤20 minutes
- [x] Verify Extractor correctly surfaces known ambiguities in benchmark papers
- [x] Internal dogfood: team uses it on their own reproduction needs
- [x] Fix critical bugs and regressions discovered during dogfood
- [x] Launch invite-gated public beta (CV-only)

---

## Phase 2 — V1 (Multi-Domain, Team-Ready, Billable)

> **Goal:** Expand beyond CV to NLP and RL domains, add team features, billing, and all deferred V1 functional requirements. Full production readiness.  
> **Exit Criteria:** Golden Dataset at 50+ papers across CV/NLP/RL, all Must + Should requirements from Doc 02 met.

### 2.1 — Multi-Domain Expansion (Doc 16 §2)
- [x] Implement NLP-specific extraction prompts & validation strategies (NFR-MAINT-02)
- [x] Implement RL-specific extraction prompts & validation strategies
- [x] Auto-detect paper domain (CV/NLP/RL) and route to domain-tuned extraction (FR-ING-04)
- [x] Expand Golden Dataset to 50+ papers spanning CV/NLP/RL proportionally
- [x] Regression-test across all domains on every prompt/graph change

### 2.2 — Full Finder Agent (Doc 08 §3.2)
- [ ] Implement embedding-based similarity ranking:
  - [ ] Embed methodology summary + candidate README/code-comments via Qdrant
  - [ ] Rank by weighted combination of embedding similarity, recency, repo-health signals
  - [ ] Log ranking weights for auditability
- [ ] Integrate PapersWithCode API for cross-reference
- [ ] Implement cross-job search cache in Qdrant/Postgres (TTL: 7 days)
- [ ] Implement human-approval checkpoint (FR-RT-02):
  - [ ] Surface top 3 candidates + "generate fresh" option
  - [ ] 24-hour auto-continue with top choice default
  - [ ] Human Approval Modal UI (glassmorphism overlay, Doc 06 §Job Progress)

### 2.3 — Full DevOps Agent (Doc 08 §3.4)
- [x] Implement `docker-compose.yml` generation for multi-service reproductions (FR-DEV-02)
- [x] Implement GPU auto-detection from architecture size/type (FR-DEV-03)
  - [x] CUDA base image + `nvidia-container-toolkit` configuration
  - [x] CPU-fallback path for smoke test where feasible
- [x] Implement full dependency-compatibility matrix (known-good CUDA/PyTorch/driver combos)

### 2.4 — Structured Fidelity Report (Doc 06 §Fidelity Report / FR-DOC-02)
- [x] Generate separate Fidelity Report artifact (extracted from README):
  - [x] Coverage breakdown (which methodology components have code, which don't and why)
  - [x] Structural check results
  - [x] Execution validation summary
  - [x] Full list of assumptions with rationale
  - [x] License/attribution disclosures for reused code
- [x] Build Fidelity Report page (long-form document-style layout):
  - [x] `CoverageBreakdownTable`
  - [x] `StructuralChecksList`
  - [x] `ExecutionValidationSummary`
  - [x] `AssumptionsList` (detailed, with rationale text)
  - [x] `LicenseDisclosurePanel` (conditional)

### 2.5 — Ingestion Expansion
- [ ] Support direct PDF upload (FR-ING-01):
  - [ ] Client-side file-type/size validation (25MB max)
  - [ ] Upload progress indicator
  - [ ] Defensive PDF parsing in isolated sandbox (Doc 12 §5)
  - [ ] Reject non-text-extractable PDFs with clear error
- [ ] Support bare arXiv ID input
- [ ] Implement user-supplied focus-scope hint (FR-ING-05, Could priority)
- [ ] Implement framework selection override (FR-GEN-05, Could priority)

### 2.6 — Workspaces, Teams & RBAC (Doc 09 §7 / FR-ACC-01–02)
- [ ] Implement organization workspace model
- [ ] Implement RBAC: Owner / Admin / Member / Billing-only roles
- [ ] Build shared authorization-decision module (single point of RBAC logic)
- [ ] Implement workspace creation/management APIs
- [ ] Build Workspace Settings page (Doc 06 §Workspace Settings):
  - [ ] Members tab: member table with role management, invite form
  - [ ] Integrations tab: GitHub App install, BYO API key (enterprise-gated placeholder)
  - [ ] Edge case: prevent last Owner from leaving/downgrading
- [ ] Update job visibility: jobs scoped to workspace, accessible by all workspace members
- [ ] Team collaboration flow: member pushes to team's shared GitHub org

### 2.7 — Billing & Usage Metering (FR-ACC-03 / Doc 09 §Billing)
- [ ] Implement usage metering per job (compute time, LLM token cost)
- [ ] Implement plan-based quota enforcement (pre-submission check)
- [ ] Integrate Stripe (or equivalent) for payment processing:
  - [ ] `POST /workspaces/{workspace_id}/billing/checkout-session`
  - [ ] Webhook handlers for payment events
- [ ] Build Billing tab in Workspace Settings:
  - [ ] Plan card
  - [ ] Usage chart (jobs over time, cost breakdown)
  - [ ] Payment method panel
- [ ] Build Usage Summary widget on Dashboard
- [ ] Implement `GET /workspaces/{workspace_id}/usage` API
- [ ] Implement Celery queue prioritization per plan tier (Doc 09 §5)

### 2.8 — GitHub Push Integration (FR-DEL-02)
- [ ] Implement GitHub App installation flow
- [ ] `POST /jobs/{job_id}/artifacts/push-to-github` endpoint
  - [ ] Push to user-authorized GitHub account/org (new repo or specified existing repo)
  - [ ] Handle auth expired, target repo exists conflicts
- [ ] Add GitHub push destination to Job Submission advanced options
- [ ] Add "Push to GitHub" button on Job Results page

### 2.9 — Personal Settings & API Keys (Doc 06 §Personal Settings)
- [ ] Build Personal Settings page:
  - [ ] Profile section
  - [ ] Connected Accounts (GitHub/Google OAuth management)
  - [ ] API Keys management (table: name, created, last used, revoke action)
  - [ ] Generate Key flow (shows raw key once)
  - [ ] Notification preferences (job-complete email/webhook)
- [ ] Implement API endpoints:
  - [ ] `POST /workspaces/{workspace_id}/api-keys`
  - [ ] `DELETE /workspaces/{workspace_id}/api-keys/{key_id}`
- [ ] API key scopes & per-request scope re-check (Doc 09 §7)

### 2.10 — Repository Explorer (Doc 06 §Repository Explorer)
- [ ] Build three-pane IDE-like layout:
  - [ ] File tree (left, ~240px, virtualized)
  - [ ] Code viewer (center, syntax highlighted)
  - [ ] Reference/annotation panel (right, ~320px, contextual)
- [ ] Implement paper-traceability annotations:
  - [ ] Inline markers in code viewer linked to paper sections/equations
  - [ ] On hover/click: show paper excerpt/figure in reference panel
  - [ ] Hover reveals traceability indicator dot in file tree (Doc 05 §6)
- [ ] File-switch cross-fade animation (150ms, Doc 05 §19)
- [ ] Default to dark mode for code viewer (Doc 06 §Repository Explorer)
- [ ] Accessible code-block markup with labeled annotations (Doc 04 §10)
- [ ] Real-time file tree growth animation during in-progress jobs (Doc 05 §14)

### 2.11 — Job Submission Advanced Options (deferred from MVP)
- [ ] Build collapsible Advanced Options panel (Doc 06 §Job Submission):
  - [ ] Target framework override `Select` (PyTorch/JAX/TensorFlow)
  - [ ] Focus scope `TextInput` (optional hint, FR-ING-05)
  - [ ] Human-approval checkpoint `Toggle` (FR-RT-02)
  - [ ] GitHub push destination `Select` (from connected GitHub App installs)
- [ ] Example papers carousel for first-time users (Doc 06 §Job Submission)

### 2.12 — Unit Test Generation (FR-GEN-04, Should priority)
- [ ] Scaffolder generates unit tests for individual components:
  - [ ] Shape checks on custom layers
  - [ ] Individual component smoke tests
- [ ] Reviewer runs generated unit tests as part of validation

### 2.13 — Notification System (Doc 09 §Notifications)
- [ ] Implement job-complete email notification
- [ ] Implement webhook notification for programmatic integrations
- [ ] Build notification bell UI in top bar
- [ ] Notification preferences in Personal Settings

### 2.14 — Infrastructure Hardening (Doc 11, V1 scope)
- [ ] Set up multi-AZ RDS (Postgres) with automatic failover
- [ ] Set up multi-AZ EKS node groups
- [ ] Configure node pools per workload: api-pool, worker-pool, gpu-pool, sandbox-pool
- [ ] Implement Kubernetes network policies for sandbox isolation
- [ ] Configure cluster autoscaling (CPU pools on request latency, GPU pool on queue depth)
- [ ] Set up monitoring: Prometheus + Grafana dashboards:
  - [ ] Engineering-ops dashboard (latency, error rate, queue depth, GPU utilization)
  - [ ] Product dashboard (reproduction success rate, fidelity score distribution, time-to-runnable)
  - [ ] Alerting on queue-depth thresholds, GPU-pool saturation, repair-loop exhaustion spikes
- [ ] Set up OpenTelemetry instrumentation across api/worker/sandbox-svc
- [ ] Structured JSON logging correlated by `job_id`/`request_id`
- [ ] Configure Postgres continuous WAL archiving + daily snapshots
- [ ] Configure MinIO versioned buckets

### 2.15 — Security Hardening (Doc 12, V1 scope)
- [ ] Implement sandboxed execution with gVisor or Firecracker (POC for GPU-passthrough compat)
- [ ] Implement strict prompt-template structure — data vs. instructions separation (Doc 12 §3)
- [ ] Output schema-validation on all agent tool calls with real-world effects
- [ ] Add adversarial test papers (prompt injection payloads) to Golden Dataset
- [ ] Implement malicious PDF detection & defensive parsing in isolated sandbox (Doc 12 §5)
- [ ] Implement secrets management via AWS Secrets Manager + CSI driver (Doc 11 §6)
- [ ] Configure TLS 1.2+ everywhere (client↔gateway, service↔service)
- [ ] Least-privilege IAM roles per service (Doc 12 §9)
- [ ] SAST/dependency scanning in CI (Doc 12 §11)
- [ ] Minimal base images (distroless), image signing + admission control

### 2.16 — Deployment Maturity (Doc 15)
- [ ] Implement blue-green deployment for API/monolith service
- [ ] Implement canary deployment for Orchestration Worker
  - [ ] Small % of new jobs to new worker version first
  - [ ] Ramp up over hours (jobs take 5–20 min to observe)
- [ ] Implement post-deploy smoke suite (fastest Golden Dataset papers + core API checks)
- [ ] Tag every deploy in OpenTelemetry/Grafana for scoped monitoring
- [ ] Set up Helm chart parameterization for dev/staging/prod environments

### 2.17 — Testing Strategy Implementation (Doc 13)
- [ ] Unit tests: high coverage on business-logic code, deterministic agent sub-components
- [ ] Integration tests: cross-module + cross-service (API ↔ Worker via Redis, Worker ↔ Sandbox)
- [ ] E2E tests (Playwright): Submission → Progress → Results, human-approval flow
- [ ] Performance/load testing (Locust/k6): target 100 concurrent jobs (NFR-PERF-03)
- [ ] Chaos engineering: kill worker mid-job (verify checkpoint resume), sandbox network partition, LLM provider outage (verify fallback)
- [ ] Golden Dataset regression gate in CI: block deploy on Fidelity Score regression

### 2.18 — V1 Launch Readiness
- [ ] Verify all Must + Should requirements from Doc 02 are met
- [ ] Verify Golden Dataset (50+ papers) meets exit criteria across all domains
- [ ] Performance benchmarking: time-to-runnable trend tracking
- [ ] Security review & penetration testing on sandbox boundary
- [ ] Write incident runbooks (GPU saturation, repair-loop spikes, LLM outage, sandbox incident)
- [ ] Define severity tiers and escalation paths (Doc 15 §7)
- [ ] Launch V1 GA — billing live, multi-domain, GTM Phase 1/2 begins

---

## Phase 3 — V2 (Gallery, Benchmarking, Enterprise Foundations)

> **Goal:** Build community loop via Public Gallery, achieve stronger trust via Benchmark Agent, begin enterprise readiness with BYO keys and compliance.

### 3.1 — Public Gallery (Doc 06 §Public Gallery / GTM Phase 2)
- [ ] `POST /jobs/{job_id}/gallery` — opt-in share (anonymous option)
- [ ] `GET /gallery` — public, no auth, cursor-paginated
- [ ] `DELETE /jobs/{job_id}/gallery` — remove from gallery
- [ ] Build Gallery page:
  - [ ] Responsive card grid (paper title, domain icon, Fidelity Score badge, submitter handle)
  - [ ] Filter bar: domain, sort by score/recency
- [ ] Handle account-deletion edge case: gallery entries persist as anonymized/orphaned unless explicit removal requested (Doc 03 §11 + GDPR compliance)

### 3.2 — Shared Read-Only Job View (Doc 06 §Shared Job View / FR-DEL-04)
- [ ] `POST /jobs/{job_id}/share-link` — generate share link (expirable, download-permission toggle)
- [ ] `GET /shared/{token}` — public read-only job view
- [ ] Build Shared Read-Only Job View page:
  - [ ] Read-only Job Results + Fidelity Report components
  - [ ] Conditional download access
  - [ ] "Powered by PaperToProd — Try it yourself" footer CTA
- [ ] Instructor-to-student and team-to-stakeholder sharing flows

### 3.3 — Benchmark Agent (Doc 08 §3.7)
- [ ] Implement Benchmark Agent:
  - [ ] Run reproduced model against paper's own reported dataset/benchmark
  - [ ] Compute quantitative fidelity delta (actual output vs. paper-reported results)
  - [ ] Report as an enhanced trust signal beyond structural/execution validation
- [ ] Integrate with Job Results page (additional fidelity dimension)
- [ ] Add benchmark results to Fidelity Report

### 3.4 — BYO LLM API Key (FR-ACC-04, enterprise)
- [ ] `POST /workspaces/{workspace_id}/integrations/byo-key`
- [ ] Envelope encryption for stored keys (per-workspace data-encryption key, Doc 12 §7)
- [ ] Keys never logged, never echoed back
- [ ] Route LLM calls through customer's own provider account when configured
- [ ] BYO API Key form in Workspace Settings Integrations tab

### 3.5 — Multi-Region DR (Doc 11 §8)
- [ ] Terraform-defined warm standby region
- [ ] RPO ≤5 min (Postgres WAL), ≤24 hrs (object storage)
- [ ] RTO ≤1 hr for core API/worker (GPU-pool cold-start acceptable)
- [ ] Cross-region S3 bucket replication for job artifacts + papers
- [ ] Postgres cross-region WAL replica

### 3.6 — SSE Streaming for CI/Programmatic Integrations (Doc 14 §11)
- [ ] `GET /jobs/{job_id}/logs` supports `Accept: text/event-stream`
- [ ] Simpler one-way stream for CI pipelines that don't need WebSocket

### 3.7 — SOC 2 Type II Initiation (Doc 12 §13)
- [ ] Formalize audit logging, access control, change-management into auditable control set
- [ ] Engage SOC 2 auditor
- [ ] Begin audit preparation (evidence collection, control documentation)

### 3.8 — Landing Page & Marketing Site (Doc 06 §Landing)
- [ ] Build hero section:
  - [ ] Headline: "Research Paper → Running Code"
  - [ ] Primary CTA: "Try it free"
  - [ ] React Three Fiber 3D visual (paper→code morph, Doc 05 §12)
  - [ ] Damped mouse-tracked camera parallax (max ~6° rotation)
  - [ ] Degrade to static illustration below 480px
- [ ] Build live proof strip (rotating recent gallery reproductions with Fidelity Scores)
- [ ] Build how-it-works section (Understand → Build → Verify):
  - [ ] GSAP ScrollTrigger scroll-storytelling (Doc 05 §23)
  - [ ] Document → pipeline nodes → code/terminal visual
- [ ] Build social proof section (logos/testimonials)
- [ ] Build pricing summary section
- [ ] Build final CTA + footer
- [ ] Background: animated gradient mesh (12–20s loop, GPU-composited, Doc 05 §17)
- [ ] Default dark mode (matches flagship AI product positioning)

### 3.9 — Cost Optimization (Doc 11 §10)
- [ ] Implement spot/preemptible GPU instances for validation workloads
- [ ] Reserved/savings-plan for steady-state CPU pools
- [ ] GPU node idle-scaling with small warm floor during off-peak
- [ ] GPU-memory-class bin-packing (match paper complexity to GPU class)
- [ ] Build Grafana cost-tracking dashboards

---

## Phase 4 — Enterprise

> **Goal:** Full enterprise readiness: on-prem/VPC deployment, compliance, SSO, audit, SLA, and continuous re-validation.

### 4.1 — On-Prem / VPC Deployment (Doc 11 §1)
- [ ] Parameterize Helm charts for on-prem/VPC-peered deployment
- [ ] Support self-hosted Postgres, Redis, object storage alternatives
- [ ] Document enterprise deployment guide
- [ ] Terraform modules for enterprise-specific infrastructure

### 4.2 — Full Audit Log & Compliance Reporting (Doc 09 §8 / Doc 10 §10)
- [ ] `audit_log_entries` table: auth events, job submissions, membership/role changes, billing changes, integration changes
- [ ] Append-only, tamper-evident audit trail
- [ ] Build Audit Log tab in Workspace Settings (enterprise-gated):
  - [ ] Virtualized, filterable audit log table
  - [ ] Cross-reference with job-level events
- [ ] Export capabilities for compliance reporting

### 4.3 — SSO (SAML/OIDC)
- [ ] Implement SAML SSO integration
- [ ] Implement OIDC SSO integration
- [ ] Enforce SSO at workspace level for enterprise customers
- [ ] Handle SSO user provisioning/deprovisioning

### 4.4 — Re-Validation Agent (Doc 08 §3.7)
- [ ] Implement scheduled re-runs of stored reproductions against updated dependency versions
- [ ] Flag drift before users encounter it (continuous re-validation)
- [ ] Enterprise-tier scheduled service
- [ ] Alerting/notification on validation drift

### 4.5 — Custom SLA Tiers & Dedicated Support
- [ ] Implement SLA tracking and reporting per enterprise workspace
- [ ] Dedicated support channels (pre-filled job ID for issue reporting)
- [ ] Custom compute ceiling configuration per enterprise plan

### 4.6 — ISO 27001 & GDPR Full Compliance (Doc 12 §13)
- [ ] Complete SOC 2 Type II certification
- [ ] Pursue ISO 27001 certification (overlapping control set with SOC 2)
- [ ] GDPR right-to-erasure full implementation:
  - [ ] Account deletion triggers cascading anonymization
  - [ ] Gallery entry removal on explicit request
  - [ ] Data processing agreements for EU customer data through LLM providers

### 4.7 — Analytics Pipeline (Doc 10 §14)
- [ ] Nightly ETL from `jobs`/`job_events` into analytics warehouse
- [ ] Anonymized/aggregated metrics for product analytics:
  - [ ] Reproduction success rate trends
  - [ ] Fidelity score distribution trends
  - [ ] Repeat usage rate tracking
  - [ ] Human-repair rate per paper category
- [ ] Product analytics dashboards in Grafana

---

## Phase 5 — Future AI Features

> **Goal:** Advanced capabilities that expand PaperToProd beyond single-paper ML reproduction.

### 5.1 — Synthesis Agent (Doc 08 §3.7 / Doc 01 §13)
- [ ] Implement multi-paper synthesis: combine methods across 2–3 related papers
- [ ] Solve methodology-conflict-resolution between incompatible approaches
- [ ] UI flow for multi-paper input and conflict visualization

### 5.2 — Non-ML Paper Domains (Doc 01 §13)
- [ ] Extend to systems/algorithms papers (database index structures, consensus protocols)
- [ ] New domain-specific extraction/validation strategies
- [ ] Evaluate generalizability of extraction/validation patterns from ML domain experience

### 5.3 — IDE-Native Experience (Doc 01 §13)
- [ ] VS Code extension for invoking PaperToProd within an existing repository
- [ ] Generate subdirectory/module rather than standalone repo
- [ ] Adapt architectural assumptions for in-repo generation

### 5.4 — Browser Extension (GTM Phase 3, Doc 01 §10)
- [ ] Chrome extension / bookmarklet for arXiv pages
- [ ] "Reproduce this with PaperToProd" button on arXiv paper pages
- [ ] One-click job submission from arXiv

---

## Technical Debt Tracker (Doc 16 §6)

> Proactively tracked debt items — to be addressed at the noted phase.

- [ ] **DevOps Agent GPU rework (V1):** MVP's CPU-only/single-GPU-profile needs real rework for V1's full auto-detection — MVP implementation should maintain clean interface boundary for this
- [ ] **Fidelity Report extraction (V1):** MVP's folded-into-README fidelity info must be mechanically extractable for V1's separate report artifact
- [ ] **Checkpoint schema consolidation (periodic):** `job_state_checkpoints` JSONB schema-versioning accumulates versions — planned consolidation every major version
- [ ] **Finder ranking weights tuning:** initial weights are heuristic — instrument and tune based on real-world Finder accuracy data post-launch
- [ ] **Event bus migration (V2+):** Redis pub/sub → Kafka if cross-service event patterns grow beyond job streaming (e.g., analytics pipeline at high volume)

---

*This plan is derived from Documents 01–16 in `E:\PaperToProd\Docs\`. Each objective traces back to specific requirements, architecture decisions, and specifications across the full documentation set. Update checkboxes as work progresses.*
