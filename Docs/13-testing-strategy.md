# PaperToProd — Document 13: Testing Strategy

**Status:** Draft v1.0
**Core challenge this strategy addresses:** most of PaperToProd's risk lives in AI-agent behavior, not conventional code paths — a passing unit-test suite says almost nothing about whether the Extractor correctly read a paper's methodology. The strategy therefore treats "AI Evaluation" (§4) as co-equal in investment to conventional testing, not an afterthought bolted onto a standard test pyramid.

---

## 1. Unit Testing

- Standard scope: individual functions/modules in the monolith (Document 9) — RBAC decision logic, quota calculation, pagination cursor handling, schema validation. Target: high coverage on business-logic-bearing code; low priority on framework glue code.
- **Agent-adjacent unit tests:** deterministic, non-LLM portions of each agent (e.g., Finder's ranking-score computation given fixed input signals, DevOps's dependency-compatibility-matrix lookup, Reviewer's error-classification routing logic) are fully unit-testable and unit-tested — only the LLM call itself is excluded from this layer (covered instead in §4).

## 2. Integration Testing

- Module-boundary tests within the monolith (e.g., Jobs module → Billing module quota-check interaction), and cross-service tests (API ↔ Orchestration Worker via the Redis pub/sub channel, Document 9 §4; Worker ↔ Sandboxed Execution Service via its API contract, Document 12 §6) run against real (ephemeral, containerized) dependencies in CI rather than mocks wherever feasible, since the inter-service *contracts* (JobState shape, event schema) are exactly where integration bugs would otherwise hide undetected until production.

## 3. End-to-End Testing

- Full user-journey tests (Document 4 §5's flows) driven via API (fast, primary CI signal) and a smaller set via browser automation (Playwright) covering the critical UI paths (Submission → Progress → Results, human-approval-checkpoint flow, GitHub push flow) — E2E-via-API runs on every PR; full browser E2E runs on a merge-to-main/pre-deploy gate given its higher runtime cost.
- **E2E jobs use a curated small/fast subset of the Golden Dataset** (§4) — tiny, fast-to-validate papers specifically chosen so E2E suite runtime stays in the minutes range, not the 20-minute median real-job time (Document 2 NFR-PERF-02) — full-scale-paper E2E runs are a separate, lower-frequency (nightly) suite.

## 4. AI Evaluation (the strategy's center of gravity)

- **Golden Dataset:** a curated, continuously-expanded set of benchmark papers (target: 50+ by GA, spanning CV/NLP/RL/other domains proportionally to expected real usage), each annotated with: ground-truth methodology breakdown (for Extractor grading), known-best reference implementation if one exists (for Finder grading), and expected fidelity-score range for a successful reproduction (for Reviewer/overall grading).
- **Per-agent eval, run on every prompt-template or graph-logic change (Document 8 §9):**
  - Extractor: methodology-extraction accuracy (precision/recall against ground-truth components) and gap-flagging recall (does it correctly flag the paper's known ambiguities rather than silently guessing).
  - Finder: ranking precision (is the known-best implementation in its top-3) and false-negative rate (defaulting to `generate_fresh` when a good implementation actually existed).
  - Scaffolder/Reviewer (evaluated jointly, since fidelity is an end-to-end property): Fidelity Score distribution across the full Golden Dataset, with a hard regression gate — no change may ship that lowers the dataset's mean Fidelity Score beyond a defined tolerance (Document 11 §5's CI gate).
- **Adversarial eval:** the injection/poisoning test papers from Document 12 §3/§4 are a permanent, growing subset of the Golden Dataset, run on the same cadence — security regression and quality regression are evaluated by the same pipeline, not two separate efforts that could drift out of sync.
- **Human-audited spot checks:** a sampled percentage of production jobs (higher rate during beta, tapering as confidence grows) are manually reviewed by an internal ML-literate reviewer against the paper, both to validate the automated Fidelity Score's own accuracy (is the metric itself measuring the right thing) and to catch failure modes the Golden Dataset hasn't yet encoded.

## 5. Performance Testing

- Load testing (Locust or k6) against the API/WebSocket layer targeting the concurrency requirement (NFR-PERF-03: 100 concurrent jobs without queueing delay beyond 2 minutes) — run pre-GA and after any significant orchestration/queueing architecture change.
- Time-to-runnable benchmarking against the full Golden Dataset on a defined cadence (weekly in CI, not just pre-release), tracked as a trend line so a gradual latency regression (e.g., from a prompt getting longer over successive edits) is caught before it silently breaches NFR-PERF-02.

## 6. Load Testing

- Covered jointly with Performance Testing (§5); additionally, GPU-pool-specific load testing (Document 11 §2/§11) to validate autoscaling behavior under a burst of GPU-requiring jobs specifically, since that resource pool's scaling latency (spinning up GPU nodes is slower than CPU nodes) is the most likely source of a real-world NFR-PERF-03 breach.

## 7. Chaos Engineering

- Deliberate fault injection targeting the platform's specific reliability requirements: kill an orchestration worker mid-job and verify LangGraph checkpoint resume works (Document 8 §4/NFR-REL-02); simulate a sandbox-service network partition and verify the Reviewer's repair loop degrades gracefully (retries with backoff, surfaces a clear error rather than hanging) rather than silently stalling a job forever; simulate primary-LLM-provider outage and verify the fallback-model chain (Document 8 §6) actually engages rather than just existing in configuration.

## 8. Regression Testing

- Conventional regression: full unit+integration suite on every PR.
- **Agent-behavior regression:** the Golden Dataset gate (§4) *is* PaperToProd's regression testing for the part of the system most likely to silently degrade — this is called out explicitly because a conventional engineering team's instinct to treat "regression testing" as purely a code-correctness concept would systematically under-test this product's actual highest-risk surface.

## 9. Security Testing

- SAST/dependency scanning in CI (Document 12 §11); periodic (at minimum, pre-GA and annually thereafter) third-party penetration testing specifically targeting the sandboxed execution boundary (Document 12 §6) given its criticality; the adversarial Golden Dataset subset (§4) as continuous automated security regression for the AI-specific attack surface (prompt injection, RAG poisoning) that a conventional pentest is less likely to probe deeply.

## 10. Smoke Testing

- Post-deploy automated smoke suite (a handful of the fastest Golden Dataset papers, plus core auth/job-submission API checks) gates production traffic cutover in the blue-green/canary deployment flow (Document 15) — must pass within a tight time budget (minutes, not the full E2E suite's runtime) since it sits directly in the deploy critical path.

## 11. Acceptance Testing

- Directly traces to Document 2 §13's acceptance criteria (e.g., ≥80% of the 20-paper benchmark reaching validated status without human intervention, median time-to-runnable ≤20 minutes) — these are the release-gating criteria for calling a version "GA-ready," distinct from and stricter than the ongoing CI regression gates (§4/§8), which protect against *regressing below* an already-achieved bar rather than defining the bar itself.

## 12. Benchmarking

- Continuous tracking (not just point-in-time) of Fidelity Score distribution, time-to-runnable, and human-repair-rate (Document 1 §11 metrics) against the Golden Dataset, visualized as trend lines in the product Grafana dashboard (Document 11 §7) — benchmarking here serves both a QA function (catching regressions) and a product function (demonstrating improvement over time to stakeholders/investors, directly supporting the credibility-driven GTM strategy in Document 1 §10).

## 13. Golden Dataset (consolidated definition)

Owned jointly by QA and the AI/ML engineering discipline (not solely either one) given it serves both conventional regression-testing and AI-evaluation purposes simultaneously; expansion process: every production failure or human-audited quality miss (§4) that reveals a gap the current dataset doesn't cover is a candidate for a new Golden Dataset entry, making the dataset a living artifact that grows in step with real-world usage rather than a fixed set defined once pre-launch.

---
*End of Document 13. Proceeding next to Document 14: API Specification.*
