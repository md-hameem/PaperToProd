# PaperToProd — Document 16: Engineering Roadmap

**Status:** Draft v1.0

---

## 1. MVP (target: prove the core loop, single-domain, narrow but real)

**Scope:** Ingestion (arXiv URL only, defer PDF upload and manual hint scoping), Extractor + Scaffolder + Reviewer agents fully built; Finder agent built but simplified (GitHub search + basic star/recency ranking, defer the embedding-similarity ranking and PapersWithCode cross-reference); DevOps agent generates Dockerfile only (defer compose/multi-service and GPU auto-detection nuance — assume CPU-only or a single fixed GPU profile); Documentation Generator produces README only (defer the separate structured Fidelity Report as a distinct artifact, fold its content into the README for MVP); no human-approval checkpoints (fully automatic pipeline); single domain focus — **computer vision papers only**, chosen because CV papers have the most standardized methodology-reporting conventions (architecture diagrams, standard datasets) of the three target domains, making extraction accuracy easiest to validate first.

**Infra scope:** single-region deployment, no DR/multi-region (Document 11 §8 deferred), no blue-green/canary sophistication (simple redeploy acceptable at this stage), Golden Dataset at ~10-15 CV papers only.

**Explicit non-goals for MVP:** teams/workspaces (single-user accounts only), billing (free/invite-only access), Gallery, GitHub push (download-only delivery).

**Exit criteria:** the Document 2 §13 acceptance criteria (≥80% validated without human intervention, ≤20 min median) achieved against the CV-only Golden Dataset subset.

## 2. V1 (target: multi-domain, team-ready, billable)

- Expand Extractor/domain-specific prompting to NLP and RL (NFR-MAINT-02's pluggability is what makes this an additive engineering effort rather than a rewrite).
- Full Finder agent (embedding-similarity ranking, PapersWithCode cross-reference, cross-job search cache).
- Full DevOps agent (compose configs, GPU auto-detection, dependency-compatibility matrix).
- Human-approval checkpoints (FR-RT-02), workspaces/teams/RBAC, billing/usage metering, GitHub push integration.
- Structured Fidelity Report as a distinct artifact/screen.
- Multi-AZ HA (Document 11 §9), still single-region.
- Golden Dataset expanded to the 50+ target (Document 13 §4).

## 3. V2

- Public Gallery + share links (GTM Phase 2 loop, Document 1 §10).
- Multi-region DR (Document 11 §8 fully realized).
- Benchmark Agent (Document 8 §3.7) — quantitative fidelity delta against paper-reported results, a materially higher trust bar than structural/execution validation alone.
- BYO-LLM-API-key enterprise option, SOC 2 Type II audit initiated (Document 12 §13).
- Programmatic API maturity (Document 14) for CI/third-party integration as a first-class supported use case, not just a technical possibility.

## 4. Enterprise

- On-prem/VPC-peered deployment option (Document 11 §1).
- Full audit log + compliance reporting surface (Document 9 §8, Document 10 §10).
- SSO (SAML/OIDC), custom SLA tiers, dedicated support.
- Re-validation Agent (Document 8 §3.7) as an enterprise-tier scheduled service (continuous drift-checking of previously reproduced repos matters most to teams with long-lived internal dependencies on generated code).

## 5. Future AI Features

- Synthesis Agent (multi-paper combination, Document 1 §13 / Document 8 §3.7) — deferred repeatedly because it requires solving methodology-conflict-resolution, a distinct and harder research problem from single-paper reproduction.
- Non-ML paper domains (systems/algorithms papers, Document 1 §13) — requires new domain-specific extraction/validation strategies analogous to but distinct from the CV/NLP/RL work, evaluated once the ML-domain product is mature and the "is the extraction/validation pattern generalizable" question can be answered from real engineering experience rather than speculation.
- IDE-native experience (Claude Code/VS Code extension, Document 1 §13) — generates into an existing repository as a module rather than a standalone repo, which changes several architectural assumptions (Document 9's scaffold-from-scratch assumption, Document 6's standalone Repository Explorer UI) enough that it's treated as a distinct workstream rather than a simple new client.

## 6. Technical Debt (anticipated, tracked proactively rather than discovered reactively)

- MVP's CPU-only/single-GPU-profile DevOps agent will need real rework (not just extension) for V1's full auto-detection — flagged now so the MVP implementation is written with that seam in mind (a clean interface boundary even if the V1 implementation behind it isn't built yet).
- MVP's folded-into-README fidelity information will need extraction into V1's distinct Fidelity Report artifact — similarly, MVP's README generation should structure this content in a way that's mechanically extractable later, not freeform prose that has to be re-authored.
- The `job_state_checkpoints.state_snapshot` JSONB schema-versioning approach (Document 10 §7) is a deliberate flexibility/rigor tradeoff that will accumulate versions over time — a planned periodic "checkpoint schema consolidation" pass (e.g., every major version) is budgeted rather than left to accumulate indefinitely.

## 7. Hiring Plan (roles, sequenced to the roadmap above — not all needed at once)

- **MVP:** 2 backend/AI engineers (comfortable across FastAPI, LangGraph, and prompt engineering — this MVP does not yet need role specialization), 1 frontend engineer (Next.js/Framer Motion), 1 founder/PM-equivalent covering product+design at MVP scale.
- **V1:** add a dedicated DevOps/infra engineer (Document 11's scope grows materially at V1), a second frontend engineer (Document 6's full page set + Document 5's motion system is substantial dedicated work), a design-system-focused designer (Document 7).
- **V2/Enterprise:** dedicated security engineer (Document 12's compliance program needs an owner distinct from generalist backend engineers), a data/analytics engineer (Document 10 §14's warehouse pipeline), enterprise-focused solutions engineer/sales-engineering hire once enterprise deals are actually in pipeline (not before — a premature enterprise hire ahead of demand is a common early-stage misallocation this plan deliberately avoids).

## 8. Milestones (illustrative sequencing, not calendar-committed here — calendar dates belong in a living project-tracking tool, not a static architecture document)

1. MVP internal dogfood (CV-only, team using it on their own reproduction needs).
2. MVP public beta (invite-gated, still CV-only) — first real external Fidelity Score data.
3. V1 GA (multi-domain, billing live) — GTM Phase 1/2 (Document 1 §10) begins in earnest.
4. V2 (Gallery live, Benchmark Agent) — GTM Phase 3 (team/lab wedge) supported by a materially stronger trust story.
5. Enterprise tier live — GTM Phase 4.

## 9. Risks (roadmap-specific, complementing Document 2 §15's product-wide risk register)

| Risk | Mitigation |
|---|---|
| CV-only MVP doesn't generalize as cleanly to NLP/RL as assumed, requiring more V1 rework than planned | NFR-MAINT-02's pluggable-domain-strategy architecture is designed *in* from MVP specifically to bound this risk, even though only one domain strategy is built initially |
| Golden Dataset quality/coverage lags real-world paper diversity, giving false confidence in CI gates | Human-audited spot-checks (Document 13 §4) as a continuous check on whether the automated Fidelity Score itself remains trustworthy, not just a one-time validation |
| Hiring plan under-resources security/compliance relative to how fast enterprise interest could materialize | Security engineer hire (§7) explicitly timed to V2, not Enterprise, so compliance groundwork (Document 12 §13) isn't started from zero once a real enterprise deal is on the table |

## 10. Budget (structural guidance, not fixed figures — actual numbers belong in a financial model, not this architecture document)

The dominant variable cost through MVP/V1 is LLM API spend (Document 8 agents) and GPU compute (Document 11 §10) — both scale with usage, which is the correct alignment for a usage-based business model (Document 1 §9), but means burn is more usage-sensitive and less flatly predictable than a typical SaaS cost structure, and should be modeled/monitored accordingly (the Grafana cost-tracking dashboards in Document 11 §7 are the operational input to that financial model, not a replacement for it).

---
*End of Document 16 — this completes the full 16-document PaperToProd architecture set.*
