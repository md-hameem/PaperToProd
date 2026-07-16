# PaperToProd — Document 8: AI Multi-Agent Architecture

**Status:** Draft v1.0
**Orchestration framework:** LangGraph (chosen over a purely linear chain or a fully autonomous open-ended agent loop — rationale in §8).

---

## 1. Overview & Design Rationale

PaperToProd's core technical risk is not "can an LLM write code" — it's **long-horizon reliability**: a job involves 6+ sequential/conditional stages, each of which can fail in ways only detectable by executing something (running code, hitting a real API), and failures must be repaired without human intervention in the common case. This shapes every decision below:

- **Explicit graph over free-form agent autonomy.** A fully autonomous "AI scientist"-style agent (plan-and-decide-everything itself) trades reliability for flexibility we don't need — the six stages (Extract, Find, Scaffold, Containerize, Validate/Repair, Document) are a known, fixed DAG with well-understood conditional branches (e.g., repair loops, human-approval pauses). Encoding this as an explicit LangGraph state machine, with each node a scoped agent, buys deterministic observability and targeted retries that a fully open-ended agent loop would not reliably provide.
- **Confidence scores as a first-class signal**, not an afterthought — because the product's differentiator (Document 1 UVP) is fidelity/trust, every agent output carries a confidence/quality signal that downstream nodes and the human-approval gate can act on, not just a final pass/fail.

## 2. Shared State Schema

A single `JobState` object threaded through the LangGraph graph (checkpointed at every node transition per NFR-REL-02):

```
JobState {
  job_id, user_id, workspace_id
  paper: { source_url, raw_text, sections[], equations[], figures[], tables[], domain_classification }
  methodology: { components[] (each: description, source_ref, confidence), gaps[] (flagged ambiguities + proposed defaults) }
  candidate_repos: [{ url, stars, last_commit, similarity_score, license }]
  chosen_repo_strategy: "generate_fresh" | "adapt_existing"
  scaffold: { file_tree, dependency_manifest, target_framework }
  generated_files: { path -> content, each tagged with source_ref comments }
  container: { dockerfile, compose_config, gpu_required }
  validation: { attempt_count, last_error, fidelity_score, per_component_status[] }
  documentation: { readme, fidelity_report }
  approvals: { checkpoint_name -> {status, timestamp, user_decision} }
  audit_log: [ {agent, action, timestamp, tokens_used, model_used} ]
}
```

This state object is the single channel of inter-agent communication — agents do not message each other directly; they read from and write to defined slices of `JobState`, which LangGraph persists at each transition (this is what makes NFR-REL-02's idempotent/checkpointed requirement achievable).

## 3. Agent Specifications

### 3.1 Extractor Agent
- **Responsibilities:** Parse paper structure; produce the `methodology` slice of `JobState` (FR-EXT-01/02/03).
- **Inputs:** `paper.raw_text`, `paper.sections/equations/figures/tables`, `paper.domain_classification`.
- **Outputs:** `methodology.components[]`, `methodology.gaps[]`.
- **Tools:** PDF/LaTeX source parser (prefers arXiv's LaTeX source over PDF-extracted text when available, since LaTeX preserves equation structure losslessly — a materially higher-fidelity input); domain-specific extraction sub-prompts (CV/NLP/RL variants, per NFR-MAINT-02's pluggability requirement).
- **Memory:** Stateless across jobs (no cross-job memory) but maintains full paper context within the job via the state object; no external long-term memory store needed for this agent.
- **Prompt strategy:** Multi-pass — pass 1 extracts a structured outline (architecture, training procedure, evaluation), pass 2 re-reads specifically for hyperparameters/config values against that outline, pass 3 self-critiques against the paper's abstract/conclusion to catch omissions (a cheap, high-value self-consistency check before handing off downstream).
- **Confidence scoring:** each `methodology.components[]` entry carries a confidence score derived from whether the value was explicitly stated (high), inferred from a citation/prior work (medium), or defaulted from general convention (low — always also added to `gaps[]`).
- **Failure handling / retries:** if pass 3's self-critique flags a major omission, Extractor re-runs pass 1/2 focused on the flagged gap (max 2 internal retries) before handing off with the gap explicitly flagged rather than looping indefinitely.
- **Human approval:** none by default (too early/granular for most users); optionally surfaced if the user enabled the approval-checkpoint toggle (Document 6), gating on low-confidence gaps specifically rather than the full extraction.

### 3.2 Finder Agent
- **Responsibilities:** Search and rank existing implementations (FR-FIND-01–04).
- **Inputs:** `paper` (title, authors, arXiv ID), `methodology.components[]` (for similarity comparison against candidate READMEs).
- **Outputs:** `candidate_repos[]`, `chosen_repo_strategy`.
- **Tools:** GitHub Search API (via a platform-owned GitHub App for higher rate limits — Document 9), PapersWithCode API, an embedding-based similarity function (methodology summary vs. candidate README/code-comment embeddings, via a vector store — Qdrant, Document 9/10) to rank beyond naive keyword/star-count matching.
- **Memory:** Maintains a platform-wide (cross-job) cache of prior searches per arXiv ID in Qdrant/Postgres, since many users will submit the same popular paper — this cache is a deliberate cost/latency optimization, refreshed on a TTL (default 7 days) so newly-published forks are still discoverable.
- **Confidence scoring:** `similarity_score` per candidate (0–1) combining README-methodology embedding similarity, recency, and repo health signals (tests/CI present, non-trivial star count) into a single ranking score with documented weights (not a black-box heuristic — weights are logged for auditability).
- **Failure handling:** if GitHub API search returns zero usable candidates (rate-limited, no results, or all candidates below a minimum similarity threshold), `chosen_repo_strategy` defaults to `generate_fresh` automatically — this is a normal, expected path, not a failure state.
- **Human approval:** default checkpoint (FR-RT-02) — user reviews top 3 candidates + the "generate fresh" option before the pipeline proceeds, with a 24-hour auto-continue-with-top-choice default per Document 3.

### 3.3 Scaffolder Agent
- **Responsibilities:** Produce the project scaffold and implementation code (FR-GEN-01–05).
- **Inputs:** `methodology`, `chosen_repo_strategy`, `candidate_repos` (if adapting), user's advanced-options overrides (target framework, focus scope).
- **Outputs:** `scaffold`, `generated_files`.
- **Tools:** Code-generation LLM calls (component-by-component, not one monolithic "write the whole repo" call — generating per methodology-component keeps each call's context focused and each output independently gradable against its specific source_ref); a static-analysis tool call (linter/import-checker) run on each generated file before handoff, to catch trivial syntax/import errors before they ever reach the execution-based validation stage (cheaper to catch here than in the Reviewer's sandboxed run).
- **Memory:** none cross-job; within-job, holds the full `methodology` and any adapted-repo code as context for consistency across generated files.
- **Confidence scoring:** each generated file inherits the confidence level of the methodology component(s) it implements, surfaced later in the Fidelity Report's coverage breakdown.
- **Failure handling / retries:** static-analysis failures trigger an immediate same-agent regeneration of just the offending file (bounded at 3 attempts) before escalating to the Reviewer's full repair loop — a cheaper, faster first line of defense than involving the full execution sandbox for a simple syntax error.
- **Human approval:** none by default (would be too granular/frequent); available as an opt-in "review generated code before validation" mode for cautious enterprise users.

### 3.4 DevOps Agent
- **Responsibilities:** Containerization (FR-DEV-01–03).
- **Inputs:** `scaffold.dependency_manifest`, `scaffold.target_framework`, methodology's compute requirements (GPU detection from architecture size/type).
- **Outputs:** `container.dockerfile`, `container.compose_config`, `container.gpu_required`.
- **Tools:** Dependency-version resolution against a maintained compatibility matrix (e.g., known-good CUDA/PyTorch/driver combinations) rather than always pulling "latest," which is a common source of silent breakage in ML environments.
- **Failure handling:** if a requested dependency combination is known-incompatible, DevOps agent substitutes the nearest known-good combination and logs the substitution as a flagged assumption (visible in the Fidelity Report per FR-DOC-02), rather than attempting the build anyway and letting it fail deep in validation.

### 3.5 Reviewer Agent (Validation & Repair)
- **Responsibilities:** Execute, validate, and drive the repair loop (FR-VAL-01–04).
- **Inputs:** Full built container image, `generated_files`, `scaffold`.
- **Outputs:** `validation.attempt_count`, `validation.last_error`, `validation.fidelity_score`, `validation.per_component_status[]`.
- **Tools:** Sandboxed execution environment (isolated, resource-limited, no network egress except explicitly allow-listed package registries — Document 12); a diff/patch tool for applying repairs to specific files rather than full regeneration where the error is localized.
- **State machine (the repair loop):** `build → run_smoke_test → (pass → compute_fidelity_score → done) | (fail → diagnose_error → route_to_responsible_agent_for_patch → rebuild)`, bounded at `max_retries` (default 5, configurable per plan tier per NFR-PERF-04's compute-ceiling logic). `diagnose_error` classifies the failure (dependency issue → route to DevOps; logic/shape error → route to Scaffolder; ambiguous → route to Scaffolder with full trace as added context) rather than blindly retrying the same agent every time.
- **Confidence scoring:** Fidelity Score (FR-VAL-03) is computed here as the weighted combination of methodology coverage %, structural-check pass rate, and execution success — the single most important computed value in the whole system, and the only one exposed as a headline user-facing number (Document 6).
- **Human approval:** none required for the repair loop itself (it's designed to be autonomous); a job that exhausts `max_retries` surfaces to the user as Partial Result (Document 3) rather than pausing mid-loop for approval, since by definition no human decision was blocking further automated progress.

### 3.6 Documentation Generator Agent
- **Responsibilities:** Produce README and Fidelity Report (FR-DOC-01/02).
- **Inputs:** Full final `JobState` (methodology, generated_files with source_refs, validation results, any license disclosures from Finder).
- **Outputs:** `documentation.readme`, `documentation.fidelity_report`.
- **Tools:** none beyond the LLM call itself — this agent is comparatively low-risk/low-complexity, since it summarizes already-validated, already-structured state rather than generating anything novel that could itself fail validation.
- **Failure handling:** minimal — a documentation-generation failure (e.g., LLM timeout) simply retries the call (up to 3 attempts) since there's no execution-based failure mode here, unlike every prior agent.

### 3.7 Future Agents (extensibility, ties to Document 1 §13 and NFR-MAINT-01)
- **Benchmark Agent:** runs the reproduced model against the paper's own reported dataset/benchmark and computes a quantitative fidelity delta (Document 1's "Benchmark-in-the-loop" future expansion).
- **Synthesis Agent:** merges methodology from multiple papers into one implementation (multi-paper synthesis, Document 1 §13) — deferred because it requires solving conflict-resolution between potentially incompatible methodologies, a materially harder problem than any single-paper agent above.
- **Re-validation Agent:** scheduled re-runs of stored reproductions against updated dependency versions to catch drift (Document 1's "Continuous re-validation").

## 4. LangGraph Design

- **Graph structure:** a directed graph with the six core agents as nodes, `JobState` as the shared/threaded state, and conditional edges implementing: Finder's human-approval branch, Scaffolder↔Reviewer's repair loop (Reviewer can route back to Scaffolder or DevOps, not just linearly forward), and a terminal branch to either "Complete" or "Partial/Failed."
- **Conditional routing example:** `Reviewer.diagnose_error` output determines the next node via a LangGraph conditional edge function reading `validation.last_error.category`, rather than a hardcoded "always go back to Scaffolder" edge — this is what makes the repair loop targeted instead of blind.
- **Checkpointing:** LangGraph's built-in state persistence (backed by Postgres, Document 10) is used directly to satisfy NFR-REL-02/03 — every node transition is a checkpoint, so a worker crash mid-job resumes from the last completed node rather than restarting the whole job.

## 5. Parallel Execution

- **Extractor and Finder run concurrently**, not sequentially: Finder's search doesn't strictly require Extractor's full output (it can begin searching on paper title/ID immediately), while its *ranking* step does benefit from Extractor's methodology summary for similarity scoring — so Finder issues its raw GitHub/PapersWithCode search calls in parallel with Extractor's first pass, then waits on Extractor's output only for the ranking/similarity sub-step. This shaves meaningful wall-clock time off the (Document 1's) time-to-runnable metric.
- **Scaffolder's per-component generation calls are parallelized** across independent methodology components (e.g., a CV paper's backbone, loss function, and data-augmentation pipeline can generate concurrently if they don't have a declared dependency on each other in the methodology graph) — bounded by a concurrency limit to manage LLM provider rate limits and cost predictability.

## 6. Fallback Models

- **Primary model:** Claude (per the tech stack) for extraction and generation (strongest at long-context technical reading and code generation with citation-style traceability).
- **Fallback chain:** on primary-provider outage or rate-limit exhaustion, the graph's model-invocation wrapper (a single shared utility, not per-agent bespoke logic) automatically retries against a secondary provider (OpenAI) with an equivalent prompt template variant — a direct mitigation for the Risk Register's "frontier LLM cost/availability shifts" risk (Document 2 §15).
- **Model routing by task:** cheaper/faster models are used for low-stakes sub-tasks (e.g., static-analysis-failure classification, log summarization for the UI) while the flagship model is reserved for extraction and code generation, where quality directly drives the Fidelity Score — a deliberate cost/quality allocation, not a blanket "cheapest model everywhere" or "best model everywhere" policy.

## 7. Prompt Templates (structure, not literal text)

Each agent's prompt template is versioned (`agent_name/vN`) and stored alongside its evaluation results (§9), following a consistent structure: **Role framing** (narrow, specific — e.g., "You are extracting methodology from an ML paper; you are not summarizing it for a general reader") → **Task-specific context** (relevant `JobState` slices only, not the entire state object, to keep context focused and cost-bounded) → **Explicit output schema** (structured, parseable, matching the `JobState` slice it will populate) → **Self-check instruction** (e.g., Extractor's pass-3 self-critique) where applicable.

## 8. Why LangGraph Over Alternatives (design rationale, as required by the quality bar)

- **vs. a single long prompt / chain-of-thought monolith:** fails the observability and targeted-retry requirements — a monolithic approach can't route a dependency error specifically back to DevOps without re-running everything.
- **vs. a fully autonomous open-ended agent (e.g., AutoGPT-style self-directed planning):** trades away reliability for a flexibility this product's well-understood, fixed six-stage workflow doesn't need; open-ended agents are demonstrably weaker at bounded, predictable long-horizon task completion than an explicit graph for a task this well-specified.
- **vs. hand-rolled state machine without LangGraph:** LangGraph specifically provides checkpointing, conditional-edge ergonomics, and streaming/observability hooks (§9) out of the box — building these from scratch would be reimplementing a substantial fraction of the framework's value with no product-specific benefit.

## 9. Evaluation

- **Golden Dataset (shared with Document 13):** a curated, growing set of benchmark papers with known-good extracted methodology and known reference implementations, used to regression-test every prompt-template version before it's promoted to production — a version that regresses Fidelity Score on the golden set is blocked from deployment automatically.
- **Per-agent offline eval:** Extractor evaluated on methodology-extraction accuracy against human-annotated ground truth; Finder evaluated on candidate-ranking precision (did it surface the actual best-known implementation in its top 3); Reviewer evaluated on repair-loop success rate per error category.

## 10. Observability

- Every LLM call, tool call, and state transition is logged to the `audit_log` slice (agent, action, timestamp, tokens used, model used) and streamed to OpenTelemetry (Document 11) for cross-job aggregate dashboards (e.g., "which agent has the highest repair-loop involvement this week" — a direct signal for where to invest prompt-engineering effort next).
- The same `audit_log` powers both the user-facing live-logs UI (Document 6) and the internal engineering observability stack — a single source of truth rather than separate user-facing and internal logging systems that could drift out of sync.

---
*End of Document 8. Proceeding next to Document 9: Backend Architecture.*
