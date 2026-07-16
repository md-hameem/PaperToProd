# PaperToProd — Document 4: UX Strategy

**Status:** Draft v1.0

---

## 1. Design Philosophy

PaperToProd's core UX tension: the product performs a genuinely long-running, uncertain, multi-step AI process (5–20+ minutes, with retries), but users evaluating an AI dev tool have near-zero patience for opacity. The philosophy is therefore **"legible latency"**: every second of wait time is spent showing the user *specifically* what is happening, in language tied to the paper they submitted, not generic spinner copy. A user should be able to glance at the screen at any point and answer "what is it doing right now, and is that expected?"

Second principle: **trust is the product, not a feature.** Every UX decision is evaluated against "does this make the user more able to judge whether they should rely on this artifact" — this is why the Fidelity Score, assumptions panel, and paper-traceability annotations are first-class UI citizens rather than buried in a README.

Third principle: **expert tool, not toy.** The audience is ML-literate. The UX should never over-explain ML concepts, but it should over-explain *what the platform itself did and why*, since that (not the ML) is the unfamiliar part for every user.

## 2. Information Architecture

```
Landing
 └─ Auth (Sign up / Log in)
     └─ Dashboard (Job History)
         ├─ Job Submission → Job Progress → Job Results / Job Failure
         │                                    ├─ Repository Explorer
         │                                    └─ Fidelity Report
         ├─ Workspace Settings
         │   ├─ Members & Roles
         │   ├─ Billing & Usage
         │   └─ Integrations (GitHub App, BYO API key)
         ├─ Personal Settings
         └─ Public Gallery (cross-cutting, also reachable pre-auth)
```

Flat, shallow hierarchy by design: no workflow requires more than 2 clicks from Dashboard. The Job (not the "project" or "paper") is the atomic unit the entire IA is organized around, since it's the unit the user actually thinks in ("my job on paper X").

## 3. Navigation

Persistent left sidebar (desktop): Dashboard, New Job (always one click away, never buried), Public Gallery, Settings. Top bar: workspace switcher (for users in multiple orgs), notification bell (job-complete alerts), account menu. No deep breadcrumb system needed given the shallow IA — a simple back-to-dashboard affordance suffices everywhere.

## 4. User Journey (primary)

1. **Discovery** — arrives via Hacker News post, a shared gallery link, or a "Reproduce with PaperToProd" browser-extension button on an arXiv page.
2. **First job (trial)** — submits without full signup friction where policy allows (or lightweight OAuth signup); watches Progress screen; this first experience is the single highest-leverage UX moment in the product and is optimized above all else for the legible-latency principle.
3. **Results evaluation** — inspects Fidelity Score and assumptions panel; this is the moment trust is won or lost.
4. **Adoption** — downloads/pushes artifact, returns days later with a second paper (the repeat-usage metric).
5. **Habit** — becomes a dashboard regular; workspace/team features become relevant once usage crosses from individual to collaborative.

## 5. User Flows / Task Flows

**Flow: Submit → Result (happy path).** Landing → New Job → paste URL → (client validates) → Submit → Progress (auto-advancing through agents) → Results → Download.

**Flow: Submit with human checkpoint.** Same as above, but Progress pauses at Finder's candidate presentation → user reviews ranked repos → approves/picks alternative → pipeline resumes.

**Flow: Failure recovery.** Progress → repair loop visible ("Attempt 2 of 5") → exhausts retries → Partial Result screen → user downloads partial scaffold and/or adjusts advanced options → re-submits.

**Flow: Team collaboration.** Member submits job → job appears in shared workspace history → teammate opens Job Results → teammate pushes to team's shared GitHub org (using workspace-level GitHub App installation, not the original submitter's personal token).

## 6. Interaction Models

- **Progressive disclosure** everywhere: advanced submission options collapsed by default; live logs collapsed by default under the friendlier pipeline visualization; fidelity report is a drill-down from the results summary, not forced reading.
- **Non-blocking human-in-the-loop:** approval checkpoints never hard-block indefinitely (24-hour auto-continue-with-defaults, per Document 3 §3), respecting that users are not always present for a multi-minute job.
- **Direct manipulation where it adds value, not everywhere:** e.g., Repository Explorer's file tree is directly navigable; the pipeline visualization is primarily observational (clicking an agent node expands its logs, but doesn't let the user "drive" the pipeline out of order, which would misrepresent the actual sequential/DAG dependency structure in Document 8).

## 7. Accessibility

- WCAG 2.1 AA baseline for all core flows (submission, progress, results).
- Color is never the sole carrier of state information (e.g., Fidelity Score uses both a numeric value and a text label, not just a green/yellow/red dot).
- All real-time progress updates are also announced via ARIA live regions so screen-reader users get equivalent "legible latency" to sighted users watching the pipeline animate.
- Motion (Document 5) respects `prefers-reduced-motion`; all functional information conveyed by animation (e.g., which agent is active) has a static-text equivalent always present, never animation-only.

## 8. Responsive Design

- Full generation workflow (Submission → Progress → Results → Repository Explorer) is desktop/tablet-optimized (≥768px); code exploration in particular is not a good mobile experience and is explicitly deprioritized there.
- Mobile viewport support is scoped to: viewing job status/notifications, reviewing a Fidelity Report, and approving a human-checkpoint decision on the go — i.e., mobile is for *monitoring and light decisions*, not initiating or deeply exploring.

## 9. Keyboard Navigation

- Full keyboard operability for submission form, dashboard table (arrow-key row navigation + Enter to open), and settings.
- Command palette (Cmd/Ctrl+K) for power users to jump to New Job, a specific past job by paper name, or Settings — appropriate for the technical, keyboard-fluent target persona.

## 10. Screen Reader Support

- Pipeline visualization exposes an equivalent linear textual status ("Step 3 of 6: Generating code") to assistive tech, not just a visual graph.
- Code viewer in Repository Explorer uses accessible code-block markup with proper labeling of the paper-traceability annotations (announced as "reference note available" rather than relying on hover-only disclosure).

## 11. Error Prevention

- Client-side input validation before any server round-trip for obviously invalid submissions (Document 3 §2).
- Confirmation dialogs for irreversible/costly actions: job cancellation mid-run (discloses partial usage billing), GitHub push to an existing repo (discloses overwrite behavior), workspace member removal.
- Quota/limit checks happen *before* job creation, not as a failure after resources are already consumed (Document 3 §2 edge case).

## 12. Human Factors & Cognitive Load

- The six-agent pipeline is real (Document 8) but the UI groups it conceptually into three user-meaningful phases — **Understand → Build → Verify** — with the six named agents nested underneath for users who want detail. This matches how the target persona (Amara, Daniel, Priya from Document 1) actually thinks about the process, rather than forcing them to learn internal agent-naming as the primary mental model.
- Numeric overload is avoided: only one headline number (Fidelity Score) is presented at a glance; supporting metrics (coverage %, structural check pass rate) are one drill-down deeper, not all competing for attention simultaneously.
- Failure messaging is written to preserve user confidence in trying again ("the repair loop tried 5 approaches and got close — here's exactly where it stopped") rather than generic apologetic copy that implies the whole approach failed.

---
*End of Document 4. Proceeding next to Document 5: Premium Motion Design Specification.*
