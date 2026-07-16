# PaperToProd — Document 2: Software Requirements Specification

**Conformance:** Structured per IEEE/ISO/IEC 29148:2018, expanded beyond the standard's minimum sections where the platform's AI-agent nature requires additional rigor (agent behavior specs, model-fallback requirements, fidelity requirements).
**Status:** Draft v1.0

---

## 1. Purpose

This SRS defines the complete functional and non-functional behavior of PaperToProd for all engineering disciplines building it: frontend, backend, AI/ML, DevOps, security, and QA. It is the contract against which the Product Functional Specification (Document 3), API Specification (Document 14), and Testing Strategy (Document 13) are all validated for consistency.

## 2. Scope

PaperToProd accepts a reference to an academic paper (arXiv URL, arXiv ID, or uploaded PDF), and produces a version-controlled, containerized software repository that implements the paper's core methodology, validated by automated execution. In scope: paper ingestion and understanding, existing-implementation discovery and comparison, code generation and scaffolding, containerization, automated execution/validation/repair, documentation generation, and delivery (downloadable archive + optional GitHub push). Out of scope for v1: multi-paper synthesis, non-ML paper domains, IDE-native generation (both deferred to Document 16 roadmap), and training-from-scratch on datasets exceeding a defined compute ceiling (v1 targets reproduction of the paper's *methodology*, not necessarily reproduction of paper-scale training runs, which may require compute beyond what the platform provisions per job by default — see NFR-PERF-04).

## 3. Definitions, Acronyms, Abbreviations

| Term | Definition |
|---|---|
| Job | One end-to-end request: paper in, validated repository out |
| Fidelity Score | Automated + optionally human-audited measure of how faithfully generated code implements the paper's stated methodology |
| Agent | An autonomous LLM-driven component with a defined role, tool access, and state (see Document 8) |
| Validation Run | The automated execution of generated code (build, install, smoke-run) used to confirm the repository is functional |
| Repair Loop | The automated cycle of: run → observe failure → diagnose → patch → re-run, bounded by a max-attempt policy |
| Scaffold | The initial project structure (directories, config, dependency manifest) before method-specific code is filled in |
| Reference Repo | An existing GitHub implementation identified by the Finder agent as a candidate source of truth or code reuse |
| RTM | Requirement Traceability Matrix |

## 4. User Classes and Characteristics

| Class | Description | Technical proficiency | Primary needs |
|---|---|---|---|
| Individual Researcher/Engineer | Solo user, personal or academic account | High (ML-literate) | Speed, fidelity, control over generation choices |
| Team Member | Belongs to an org workspace | High | Shared history, collaboration, private repo integration |
| Team Admin | Manages org workspace, billing, seats | Medium–High | Access control, usage visibility, cost governance |
| Enterprise Compliance/Security Reviewer | Rarely uses the product directly, reviews it | Medium (security-focused, not necessarily ML) | Audit logs, data handling guarantees, sandboxing evidence |
| Instructor | Assigns reproductions to students | High | Batch job submission, shareable read-only links |
| Anonymous/Trial User | Unauthenticated or freshly signed up | Variable | Fast time-to-first-value, generous but bounded trial |

## 5. Functional Requirements

Numbering: `FR-<AREA>-<NN>`. Priority per MoSCoW (Must/Should/Could/Won't) — cross-referenced in §12 Priority Matrix.

### 5.1 Ingestion
- **FR-ING-01 (Must):** System shall accept an arXiv URL, bare arXiv ID, or direct PDF upload as job input.
- **FR-ING-02 (Must):** System shall fetch and parse the paper's full text, section structure, equations (LaTeX where extractable from arXiv source), figures, and tables.
- **FR-ING-03 (Must):** System shall detect and reject non-reproducible inputs (e.g., a purely theoretical/survey paper with no methodology to implement) with a clear user-facing explanation rather than silently producing a low-quality output.
- **FR-ING-04 (Should):** System shall detect the paper's primary domain (CV, NLP, RL, etc.) to route to domain-tuned extraction prompts and validation strategies.
- **FR-ING-05 (Could):** System shall accept a user-supplied hint (e.g., "focus on Section 4.2 only") to scope extraction.

### 5.2 Understanding / Extraction (Extractor Agent — see Document 8)
- **FR-EXT-01 (Must):** System shall produce a structured methodology representation: architecture components, data flow, loss functions, hyperparameters, training procedure, and evaluation protocol, each tagged with its source location (section/page/equation number) in the paper.
- **FR-EXT-02 (Must):** System shall flag methodology details that are ambiguous or missing from the paper (e.g., unspecified batch size) rather than silently inventing values without disclosure.
- **FR-EXT-03 (Should):** For flagged gaps, system shall propose a reasoned default (e.g., "value not stated; using the value from the paper's cited prior work X, or a common default for this architecture family") and surface the assumption to the user.

### 5.3 Discovery (Finder Agent)
- **FR-FIND-01 (Must):** System shall search GitHub (and where available, PapersWithCode) for existing implementations of the same paper.
- **FR-FIND-02 (Must):** System shall rank candidate repositories by signals including: star count, recency of last commit, presence of a working test/CI badge, and textual similarity between repo README and paper methodology.
- **FR-FIND-03 (Should):** System shall present the top candidates and its selection rationale to the user before deciding whether to adapt an existing repo or generate from scratch (configurable to fully automatic for API/batch users).
- **FR-FIND-04 (Must):** When reusing code from an existing repository, system shall preserve and surface that repository's license and attribution requirements to the user.

### 5.4 Generation / Scaffolding (Scaffolder Agent)
- **FR-GEN-01 (Must):** System shall generate a complete project scaffold: dependency manifest, directory structure, entry points, and configuration, appropriate to the detected domain and chosen framework (default PyTorch unless the paper's own released code or the user specifies otherwise).
- **FR-GEN-02 (Must):** System shall generate implementation code for each methodology component identified in FR-EXT-01, with inline comments citing the paper section/equation each block implements.
- **FR-GEN-03 (Must):** System shall generate a minimal runnable example (a smoke-test script or notebook) that exercises the core forward pass / pipeline without requiring the full paper-scale dataset or compute.
- **FR-GEN-04 (Should):** System shall generate unit tests for individual components (e.g., shape checks on a custom layer) in addition to the end-to-end smoke test.
- **FR-GEN-05 (Could):** System shall support user-selected target frameworks (PyTorch, JAX, TensorFlow) where the paper's domain makes this a meaningful choice.

### 5.5 Containerization & DevOps (DevOps Agent)
- **FR-DEV-01 (Must):** System shall generate a Dockerfile that builds a working container image for the scaffold, pinning all dependency versions.
- **FR-DEV-02 (Must):** System shall generate a `docker-compose.yml` or equivalent when the reproduction requires auxiliary services (e.g., a vector store, a Redis cache) to run.
- **FR-DEV-03 (Should):** System shall detect and configure GPU passthrough (CUDA base image, `nvidia-container-toolkit` assumptions) when the paper's methodology requires GPU acceleration, and generate a CPU-fallback path for the smoke test where feasible.

### 5.6 Validation & Repair (Reviewer Agent)
- **FR-VAL-01 (Must):** System shall build the generated container image and execute the smoke-test script inside it in an isolated sandboxed environment.
- **FR-VAL-02 (Must):** On failure, system shall capture the full error trace, feed it back into a repair loop with the responsible agent, and re-attempt, bounded by a configurable max-retry count (default 5) before surfacing the failure to the user with full logs.
- **FR-VAL-03 (Must):** System shall compute and report a Fidelity Score for the final artifact, combining: (a) coverage — % of extracted methodology components with corresponding generated code, (b) structural checks — do declared shapes/dimensions match the paper's stated architecture, (c) execution success.
- **FR-VAL-04 (Should):** System shall run any user-approved additional validation (e.g., a short training run against a small public dataset) when compute budget allows, comparing high-level output characteristics (loss decreasing, output shapes, sanity metrics) against what the paper reports.

### 5.7 Documentation (Documentation Generator Agent)
- **FR-DOC-01 (Must):** System shall generate a README covering setup, usage, an explanation of the implementation's mapping to the paper, and known limitations/assumptions (surfacing everything flagged in FR-EXT-02).
- **FR-DOC-02 (Should):** System shall generate a "fidelity report" document distinct from the README, itemizing every assumption made and every gap between paper and code.

### 5.8 Delivery & Workspace
- **FR-DEL-01 (Must):** System shall provide the completed repository as a downloadable archive.
- **FR-DEL-02 (Should):** System shall support pushing the repository directly to a user-authorized GitHub account/org (new repo or specified existing repo).
- **FR-DEL-03 (Must):** System shall persist job history (inputs, intermediate agent outputs, final artifacts, logs) per user/workspace, retrievable later.
- **FR-DEL-04 (Should):** System shall support sharing a read-only link to a job's results (for instructors sharing with students, or team members sharing with stakeholders).

### 5.9 Realtime Progress & Collaboration
- **FR-RT-01 (Must):** System shall stream real-time job progress (current agent, current step, logs) to the client over WebSocket.
- **FR-RT-02 (Should):** System shall allow a user to pause a job at defined checkpoints (e.g., after Finder's candidate presentation) for human approval before continuing (see Document 8, Human Approval).

### 5.10 Account, Auth, Billing
- **FR-ACC-01 (Must):** System shall support authentication via OAuth (GitHub, Google) and email/password.
- **FR-ACC-02 (Must):** System shall support organization workspaces with role-based access control (Owner, Admin, Member, Billing-only).
- **FR-ACC-03 (Must):** System shall meter usage per job (compute time, LLM token cost) and enforce plan-based quotas.
- **FR-ACC-04 (Should):** System shall support bring-your-own-API-key configuration for enterprise customers who want to route LLM calls through their own contracted provider account.

## 6. Non-Functional Requirements

### 6.1 Performance
- **NFR-PERF-01:** Median time-to-first-progress-update after job submission ≤ 10 seconds.
- **NFR-PERF-02:** For a "typical" paper (single-architecture CV/NLP paper, <15 pages), median end-to-end time-to-validated-artifact ≤ 20 minutes.
- **NFR-PERF-03:** System shall support at least 100 concurrent jobs per deployment region at GA without queueing delay exceeding 2 minutes.
- **NFR-PERF-04:** System shall enforce a default per-job compute ceiling (configurable per plan) and shall degrade gracefully — delivering the best-effort artifact plus a clear explanation — rather than failing silently when a paper's full-scale reproduction exceeds that ceiling.

### 6.2 Reliability & Availability
- **NFR-REL-01:** Core API and job-submission path shall target 99.9% monthly availability.
- **NFR-REL-02:** No single agent failure shall corrupt job state such that a retry is impossible; all agent steps shall be idempotent or checkpointed.
- **NFR-REL-03:** System shall preserve all intermediate artifacts of a failed job for at least 30 days for debugging and support purposes.

### 6.3 Security
- **NFR-SEC-01:** All generated code execution shall occur in a network-isolated, resource-limited sandbox (see Document 12) with no access to platform secrets or other tenants' data.
- **NFR-SEC-02:** Uploaded PDFs shall be scanned and parsed defensively against malicious file structures before being passed to any agent (see Document 12, Malicious PDFs).
- **NFR-SEC-03:** All inter-agent and agent-tool communications shall be logged in a tamper-evident audit trail for enterprise tenants.

### 6.4 Fidelity & Trustworthiness (platform-specific, beyond standard NFR categories)
- **NFR-FID-01:** Every generated code file shall carry traceability comments linking back to specific paper sections, satisfying FR-GEN-02.
- **NFR-FID-02:** The platform shall never present an unvalidated artifact (one that has not passed at least the smoke-test validation run) as "complete" — partial/failed jobs must be visibly and unambiguously marked as such in both UI and API responses.

### 6.5 Usability & Accessibility
- **NFR-UX-01:** Core workflows shall meet WCAG 2.1 AA (detailed in Document 4).
- **NFR-UX-02:** A first-time user shall be able to submit their first job within 60 seconds of landing on the product, unauthenticated where trial policy allows.

### 6.6 Maintainability & Extensibility
- **NFR-MAINT-01:** New agent types (per Document 8's "Future Agents") shall be addable without modifying the core orchestration graph's existing node contracts.
- **NFR-MAINT-02:** Domain-specific extraction/validation strategies (CV vs. NLP vs. RL) shall be pluggable, not hardcoded into a monolithic prompt.

### 6.7 Portability
- **NFR-PORT-01:** Generated repositories shall not depend on any PaperToProd-proprietary runtime; they must be runnable standalone by a user who never returns to the platform.

## 7. External Interfaces

- **User Interface:** Web application (Next.js), responsive down to tablet width; mobile is view-only for job status (full generation flows require a desktop-class viewport per Document 4).
- **APIs consumed:** arXiv API (metadata + source), GitHub REST/GraphQL API (search, repo content, push), PapersWithCode API (cross-reference), LLM provider APIs (OpenAI, Anthropic — see Document 8 Fallback Models).
- **APIs provided:** PaperToProd REST + WebSocket API (Document 14), enabling third-party/CI integration (e.g., a lab's internal tool submitting jobs programmatically).
- **Storage interfaces:** Object storage (generated repositories, logs, PDFs) — see Document 10/11.

## 8. Operating Environment

- Cloud-hosted, containerized deployment (Kubernetes) — see Document 11. Client: modern evergreen browsers (Chrome, Firefox, Safari, Edge — last 2 major versions). No native desktop/mobile app in v1.

## 9. Constraints

- LLM API rate limits and cost bound the platform's default per-job token budget; behavior when exceeded must degrade per NFR-PERF-04.
- GitHub API rate limits (especially for unauthenticated-on-behalf-of-user search) constrain Finder agent throughput — mitigated via platform-level GitHub App authentication with higher limits (Document 8, Document 9).
- Sandboxed execution requires GPU-capable nodes for many papers, which are a distinct, more expensive, and more capacity-constrained resource pool than CPU nodes — this shapes both cost model (Document 1 §9) and infra design (Document 11).

## 10. Assumptions

- Users submitting papers have baseline ML literacy sufficient to evaluate the output; the platform is not attempting to explain ML fundamentals.
- The majority of target papers have either an arXiv listing or a PDF conforming to standard academic paper structure (abstract, sections, references) — non-standard document formats are explicitly out of scope for v1 parsing guarantees.
- GitHub remains the dominant public code-hosting platform for research code during the v1–v2 horizon (see Document 16 for re-evaluation trigger).

## 11. Dependencies

- Availability and terms-of-service compliance of arXiv, GitHub, and PapersWithCode APIs.
- Continued availability of frontier LLM APIs at a cost structure compatible with the usage-based business model (Document 1 §9) — a material dependency flagged again in the Risk Register below.

## 12. Priority Matrix (MoSCoW Summary)

| Priority | Requirement count (approx., this document) | Release target |
|---|---|---|
| Must | 27 | MVP |
| Should | 10 | V1 |
| Could | 3 | V1/V2 |
| Won't (this release) | Multi-paper synthesis, non-ML domains, native IDE plugin | V2+/Future (Document 16) |

## 13. Acceptance Criteria (representative sample — full set lives in Document 13's Golden Dataset)

- **AC for FR-VAL-01/02:** Given 20 curated benchmark papers spanning CV, NLP, and RL, ≥ 80% shall reach a validated (smoke-test-passing) artifact without human intervention within the default retry budget.
- **AC for FR-EXT-02:** For a benchmark paper with at least one known ambiguous/missing hyperparameter, the system's assumption-flagging shall surface that specific gap (verified by manual audit against the benchmark's known-gaps annotation).
- **AC for NFR-PERF-02:** Measured against the same 20-paper benchmark, median wall-clock time-to-validated-artifact shall not exceed 20 minutes.

## 14. Requirement Traceability Matrix (excerpt — full matrix maintained as a living spreadsheet linked from this doc)

| Req ID | Source (Doc 1 driver) | Design doc | Test coverage (Doc 13) |
|---|---|---|---|
| FR-ING-01 | UVP: "Paste a paper" | Doc 3 §Screen: Submission, Doc 14 §POST /jobs | E2E-ING-01 |
| FR-EXT-01/02 | UVP: fidelity/traceability | Doc 8 §Extractor Agent | Golden-Dataset fidelity audit |
| FR-FIND-01/02 | Problem Statement: fragmentation tax | Doc 8 §Finder Agent | Integration-FIND-01 |
| FR-VAL-01/02/03 | North Star metric | Doc 8 §Reviewer Agent, Doc 12 §Sandboxed Execution | E2E-VAL-01, Chaos-VAL-01 |
| NFR-SEC-01/02 | Security Architecture | Doc 12 | Security test suite |

## 15. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Frontier LLM cost/availability shifts unfavorably | Medium | High | Multi-provider fallback (Doc 8), BYO-key enterprise option (FR-ACC-04) |
| Papers with insufficiently-detailed methodology cause systematically low fidelity scores | High (inherent to the domain) | Medium | Explicit gap-flagging (FR-EXT-02/03) turns a silent failure mode into a disclosed, trust-preserving one |
| Malicious/adversarial PDF or prompt-injected paper content compromises an agent | Low–Medium | High | Sandboxing, PDF defensive parsing, prompt-injection mitigations (Doc 12) |
| GitHub API rate limiting throttles Finder agent at scale | Medium | Medium | Platform-level GitHub App with higher rate ceiling; caching of prior searches |
| Generated code silently violates a reused repo's license terms | Low | High (legal/reputational) | Mandatory license surfacing (FR-FIND-04), license-compatibility check before code reuse |
| Users over-trust an unvalidated or partially-validated artifact | Medium | High (core trust proposition) | Hard UI/API rule (NFR-FID-02): no artifact is presented as complete without passing validation |

---
*End of Document 2. Proceeding next to Document 3: Product Functional Specification.*
