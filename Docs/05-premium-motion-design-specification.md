# PaperToProd — Document 5: Premium Motion Design Specification

**Status:** Draft v1.0
**Mandate:** The interface must read as a flagship AI product (OpenAI / Linear / Arc / Vercel / Anthropic tier), never as a CRUD dashboard. Every animation below is justified by a usability function, not decoration for its own sake — decorative-only motion is explicitly excluded.

---

## 1. Motion Principles

1. **Motion communicates state change, not just presence.** If something animates, it's because something *actually changed* (a new agent became active, a value updated, an error occurred). Ambient decoration is allowed only in genuinely idle backgrounds (e.g., landing page), never layered onto functional UI in a way that could be mistaken for a state signal.
2. **Latency becomes narrative.** Because jobs run 5–20+ minutes, the Progress screen's motion design is the single highest-investment area in the whole product — it is the tool that makes "legible latency" (Document 4 §1) actually land emotionally, not just informationally.
3. **Physically plausible, never bouncy-for-its-own-sake.** Spring curves are tuned to feel like weighted physical objects settling, not cartoonish overshoot — matching the restrained, confident feel of Linear/Vercel rather than a consumer social app.
4. **Motion respects the user's agency.** Nothing animates in a way that blocks or delays an action the user is trying to take (e.g., a button never has a mandatory 400ms animation before it's clickable). `prefers-reduced-motion` is respected everywhere by substituting instant or fade-only transitions for anything non-essential.

## 2. Motion Hierarchy

Three tiers, each with a distinct timing/easing vocabulary so the eye can distinguish importance at a glance:

- **Tier 1 — System state (highest priority):** agent pipeline transitions, validation pass/fail, job completion. Duration 400–600ms, custom spring (see §4), always accompanied by a persistent (non-animated) text/state equivalent for accessibility.
- **Tier 2 — Component feedback:** button presses, card hovers, input focus. Duration 120–200ms, standard ease-out.
- **Tier 3 — Ambient/atmospheric:** background gradients, particle fields on marketing/landing surfaces. Slow (8–20s loops), low-contrast, fully suppressible via `prefers-reduced-motion` since it carries zero functional information.

## 3. Animation Timing (reference table)

| Interaction class | Duration | Easing |
|---|---|---|
| Micro (hover, focus ring) | 120ms | ease-out (cubic-bezier(0.16, 1, 0.3, 1)) |
| Button press | 100ms down / 150ms up | ease-in-out |
| Card entrance (list/grid) | 250ms, staggered 30ms/item | ease-out |
| Panel expand/collapse (advanced options, logs) | 250–300ms | spring (see §4) |
| Agent node state change (pipeline) | 450ms | spring, slightly underdamped for a felt "settle" |
| Screen-level transition (route change) | 300ms | ease-in-out with cross-fade + 8px slide |
| Success celebration (job complete) | 600–900ms one-shot | spring, single overshoot only |
| Failure state entrance | 300ms | ease-out, no overshoot (overshoot on a failure state reads as flippant) |

## 4. Physics & Spring Curves

Standard spring token set (Framer Motion `type: "spring"` config), used consistently rather than ad hoc per-component tuning:

- **`spring.snappy`** — stiffness 500, damping 30 — for micro-interactions (hover, toggle).
- **`spring.settle`** — stiffness 220, damping 24 — for panel/card entrances; slight, tasteful overshoot.
- **`spring.pipeline`** — stiffness 180, damping 20 — deliberately the "weightiest" spring, reserved for agent-node state transitions, so the pipeline visualization feels like the substantive core of the product rather than a peripheral widget.
- **`spring.celebration`** — stiffness 260, damping 16 — the only spring allowed a visible bounce, reserved exclusively for job-completion success, so that moment is motion-differentiated from everything else in the product.

## 5. Micro-Interactions

- **Submission input:** on valid-format detection, a subtle border-color shift + a checkmark icon that draws in via SVG stroke-dashoffset animation (200ms) — confirms validity without an intrusive success toast.
- **Copy-to-clipboard (job ID, share link):** icon morphs from copy-icon to checkmark and back after 1.5s, via a shared-layout crossfade, not a separate toast component — keeps confirmation spatially tied to the action.
- **Toggle switches (advanced options):** thumb travel uses `spring.snappy`; track color transitions via a 150ms linear color interpolation, decoupled timing from the thumb's spring so the two don't look mechanically identical (a deliberate "premium" detail — cheap toggles animate everything in lockstep).

## 6. Hover Interactions

- **Dashboard job-history rows:** on hover, row elevates 2px (box-shadow transition, 150ms) and reveals row-level quick actions (re-run, share) via an opacity+8px-slide-in, staggered 20ms between icons.
- **Repository Explorer file tree:** hover reveals a paper-traceability indicator dot next to files that carry reference annotations, fading in over 150ms — a discoverability affordance for the product's signature trust feature, made present but not noisy.
- **Fidelity Score card:** hover triggers a subtle parallax tilt (max 4°, tied to cursor position via a damped spring, not raw 1:1 tracking) reinforcing the "flagship" tactile feel on the single most important number in the product.

## 7. Focus Animations

- Focus rings use a 2px offset outline that animates in via scale (0.95→1) + opacity over 120ms rather than an abrupt browser-default outline — must remain fully visible and WCAG-compliant in contrast, motion is additive polish only, never a replacement for a static visible focus indicator.

## 8. Loading Animations

- **Skeleton loading:** shimmer gradient sweep (1.5s loop, ease-in-out, low amplitude) on dashboard rows, repository file tree, and fidelity report sections while data streams in — never a bare spinner for content-shaped regions.
- **Agent "thinking" state:** within an active pipeline node, a soft pulsing glow (2s loop, opacity 0.4↔0.8) indicates "agent is actively processing" distinct from the one-time 450ms transition that marks *becoming* active — the pulse is the sustained-state signal, the spring transition is the change-of-state signal, and the two are never conflated into one animation.

## 9. Success Animations

- **Job completion:** the active pipeline node completes its 450ms `spring.pipeline` settle, then the whole pipeline bar collapses/morphs (shared-layout animation, 500ms) into a single "Complete" summary card using `spring.celebration` — a literal visual condensation of the whole process into its result, reinforcing the product's core promise ("all that work → this artifact").
- **Fidelity Score reveal:** the number counts up (not appears instantly) over 800ms with an ease-out curve, synchronized with a radial progress ring draw — counting up is used deliberately (not merely decorative) because it gives the user a half-second to anticipate and register the number rather than react to a sudden value.

## 10. Failure Animations

- Failed agent node: color transitions to the failure token over 200ms linear (no spring, no overshoot — deliberately calmer/flatter than any success motion, per Motion Principle 4, so failure never feels punitive or alarming).
- Partial-Result screen entrance: components fade/slide in individually but *without* the staggered celebratory rhythm used on Results — same directional language (bottom-to-top, per §3) but slower and unstaggered, so the two "arrival" moments are motion-distinguishable at a glance even before reading any text.

## 11. Glass Morphism, Lighting, Depth

- Reserved for elevated/overlay surfaces only (modals, the advanced-options panel, command palette) — a translucent frosted background (backdrop-blur 20px, background opacity ~70% of surface token) with a 1px inner-highlight border simulating a light source from the top-left, consistent across all glass surfaces so the "light source" reads as a coherent property of the whole UI rather than a per-component accident.
- Depth is communicated primarily through a 3-tier elevation shadow system (Document 7) plus the glass treatment above — not through literal 3D transforms on flat UI, which is reserved for the pipeline visualization specifically (§13).

## 12. 3D Interaction / Parallax / Mouse Tracking

- Landing page hero: a lightweight React Three Fiber scene — an abstract representation of "paper becoming code" (e.g., stylized floating document-plane morphing into a structured node/graph form) with damped mouse-tracked camera parallax (max ~6° rotation, heavily damped spring so it never feels twitchy).
- Explicitly *not* used in-app during functional workflows (Submission/Progress/Results) — 3D/parallax is a marketing-surface technique in this product, since introducing camera-parallax motion into a screen the user is relying on for functional information (e.g., Progress) would undermine Motion Principle 1.

## 13. Agent Visualization (signature system-level animation)

This is the single most important animated system in the product — it's what makes the multi-agent architecture (Document 8) *visible and legible* rather than an invisible backend abstraction.

- Rendered as a horizontal DAG of nodes (Extractor → Finder → Scaffolder → DevOps → Reviewer → Documentation Generator), built in SVG (not R3F — this needs pixel-crisp text/iconography and accessibility hooks, not 3D).
- **Idle/pending node:** low-opacity outline only.
- **Active node:** fills with the agent's assigned accent color (Document 7 palette), pulsing glow per §8, connecting edge to the *next* node animates a traveling light/dash-offset pulse (indicating "work is flowing toward this next stage," subtly previewing what's coming).
- **Complete node:** settles to a solid filled state with a small checkmark draw-in (SVG stroke animation, 200ms), connecting edge to the *previous* node solidifies fully (no longer animated) — a completed edge is visually "done," an edge leading into the active node is "alive."
- **Failed/retrying node:** distinct amber pulse (not the calm blue/purple "active" pulse) with a small retry-count badge that increments with a brief scale-pulse (not a full re-animation of the whole node) each retry attempt — keeps the repair loop legible without being visually chaotic on attempt 4 of 5.

## 14. Repository Generation Animation

- As the Scaffolder/agent produces files, the Repository Explorer's file tree (when open during an in-progress job) animates new file/folder nodes into the tree via a staggered fade+8px-slide (matching §3's card-entrance token), giving a felt sense of the repo "growing" in real time rather than appearing all at once at job completion.

## 15. Progress Animation (overall job progress)

- A persistent slim top-of-viewport progress bar (distinct from the pipeline visualization, which is architectural/informational) — animates width via `spring.settle`, never regresses backward even during a repair-loop retry (retries are communicated via the pipeline visualization's amber state, not by the top-level bar going backward, which would read as literal negative progress and undermine trust).

## 16. Realtime Graph Visualization

- Live log panel, when expanded, renders incoming log lines with a typewriter-adjacent reveal (lines fade+slide in as they arrive over the WebSocket, not instantly appended) — capped at a max reveal rate so a burst of buffered logs doesn't create a jarring scroll-flood; excess buffered lines beyond the cap append instantly once the cap is reached, prioritizing legibility of the *live* portion over animating a backlog.

## 17. Background Animations

- Landing/marketing surfaces only: slow animated gradient mesh (12–20s loop, GPU-composited via CSS `background-position`/transform only, never triggering layout) as an ambient backdrop behind the R3F hero — functional app surfaces (Dashboard, Progress, Results) use a static, subtly-textured background with zero ambient motion, to keep functional screens calm and legible per Motion Principle 1.

## 18. Skeleton Loading

Covered in §8; additionally: skeleton shapes must match the *actual* shape of the content they precede (e.g., a Fidelity Score skeleton is a circular ring shape, not a generic rectangle) so the loading state itself previews the coming layout and reduces perceived wait (a known, evidence-backed UX pattern, not merely aesthetic).

## 19. Code Rendering Animation

- Repository Explorer's code viewer: switching files cross-fades content (150ms) rather than an abrupt swap; syntax highlighting applies instantly (no animated "typing" of code — a typewriter effect on *reading* code would actively harm usability by delaying the user's ability to scan, which would violate Motion Principle 1).

## 20. Terminal / Live Logs Animation

- Terminal-styled panel (monospace, dark background regardless of overall light/dark mode, per convention) with a blinking cursor only while a log stream is actively open and receiving data; cursor stops blinking (solid) once a stream closes, giving a clear "this stream is finished" signal without needing supplementary text.

## 21. Transitions (route/screen level)

- Cross-fade + 8px vertical slide (300ms ease-in-out) between major screens, consistent direction (new content enters from a slightly lower position, implying forward progress through the product) — reused identically across Submission→Progress, Progress→Results, Dashboard→any detail screen, so the transition language is a learned, predictable system rather than novel per screen.

## 22. Recommended Technologies

| Need | Technology | Why |
|---|---|---|
| Component-level motion (React) | Framer Motion | Declarative, first-class spring physics, shared-layout animations (used extensively above for morph/condense effects) |
| Complex/sequenced timelines (e.g., success-celebration sequence, landing scroll storytelling) | GSAP (+ ScrollTrigger) | More precise sequencing/scrubbing control than Framer Motion for multi-step choreographed sequences |
| Marketing hero 3D scene | Three.js via React Three Fiber | Declarative React integration; damped mouse-parallax camera composable with existing spring vocabulary |
| Pre-built celebratory/complex vector animations (if design team produces them in After Effects) | Lottie | Only where a designer-authored vector animation is more efficient than hand-coding (e.g., a bespoke completion illustration) — not used for anything covered by the systematic spring/SVG approach above, to avoid two parallel motion systems |
| Ambient landing-page gradient/shader background | Custom WebGL/shader (lightweight, via R3F `shaderMaterial` or plain GLSL) | GPU-composited, avoids the performance cost of a DOM/CSS-only animated gradient at that visual complexity |

## 23. Scroll Storytelling (landing page only)

- Marketing landing page uses GSAP ScrollTrigger to choreograph the "paper → agents → code" narrative as the user scrolls: a document visual scrolls into a pipeline of glowing nodes (reusing the exact visual language of §13's in-app pipeline, deliberately, so the marketing page is a preview/rehearsal of the real in-app experience rather than a disconnected marketing fiction) → resolves into a code/terminal visual. Entirely absent from authenticated in-app screens.

---
*End of Document 5. Proceeding next to Document 6: Complete UI Design Specification.*
