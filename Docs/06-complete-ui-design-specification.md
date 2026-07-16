# PaperToProd — Document 6: Complete UI Design Specification

**Status:** Draft v1.0
**Note:** This document specifies structure, hierarchy, and behavior per page to a level a designer could take directly into Figma. Token values (exact colors, exact spacing scale) are defined once in Document 7 (Design System) and referenced here by name rather than duplicated.

---

## Global Layout Shell

**Structure:** Fixed left sidebar (240px expanded / 64px collapsed) + top bar (56px) + main content area. Sidebar collapses to icon-only on tablet widths; becomes a bottom-sheet-triggered drawer below 768px (mobile monitoring use case per Document 4 §8).

**Top bar contents:** workspace switcher (left, next to sidebar), page title (center-left), notification bell + account menu (right).

**Design tokens used:** `color.surface.base`, `color.surface.raised`, `elevation.1` for top bar shadow, `spacing.4` gutter padding.

---

## Page: Landing (Marketing)

**Purpose:** Convert cold traffic (Document 1 GTM Phase 1/2) into a first job submission.

**Sections (top to bottom):**
1. Hero — headline ("Research Paper → Running Code"), sub-headline, primary CTA ("Try it free"), R3F 3D visual (Document 5 §12).
2. Live proof strip — rotating examples of recently/publicly reproduced papers with their Fidelity Scores (pulls from Public Gallery data), building immediate credibility.
3. How-it-works — three-step visual (Understand → Build → Verify, matching Document 4's user-facing mental model) with the scroll-storytelling treatment (Document 5 §23).
4. Social proof — logos/testimonials (placeholder until real customers exist).
5. Pricing summary (links to full pricing page, not detailed here).
6. Final CTA + footer.

**Component hierarchy:** `Hero > (Headline, SubHeadline, CTAButton, R3FCanvas)`; `ProofStrip > ProofCard[]`; `HowItWorks > StepCard[3]`.

**Responsive:** R3F hero degrades to a static illustration below 480px width (avoid mobile GPU/battery cost for marginal visual gain — Document 5's 3D usage is explicitly a desktop-marketing technique).

**Dark/Light:** Landing defaults to dark mode (matches the "flagship AI product" positioning of Linear/Vercel/Arc-style sites) but respects system preference.

---

## Page: Sign Up / Log In

**Layout:** Centered single-column card, max-width 400px, on the same ambient (but static, non-3D) background treatment as the app shell.

**Components:** OAuth buttons (GitHub primary — matches the developer audience and enables immediate GitHub App linkage; Google secondary), divider, email/password form, toggle link between sign-up/log-in modes.

**States:** default, submitting (button shows inline spinner replacing label text, not a separate overlay), error (inline, field-level where applicable — e.g., "email already in use" under the email field, not a generic top-of-form banner for field-specific errors), success (brief checkmark micro-interaction before redirect to Dashboard or, for first-time users, directly to Job Submission).

---

## Page: Job Submission

**Layout:** Centered, generous whitespace, single primary input dominating the fold — deliberately the least "dashboard-like" screen in the product, reinforcing that this is the product's single moment of maximum focus.

**Wireframe (desktop, ASCII approximation):**
```
[ Sidebar ] [ Top bar: "New Job"                                    ]
            [                                                        ]
            [        Paste an arXiv URL, ID, or upload a PDF         ]
            [   ┌──────────────────────────────────────────────┐    ]
            [   │  [input field with tab toggle: URL | Upload]  │    ]
            [   └──────────────────────────────────────────────┘    ]
            [              [ Advanced options ▾ (collapsed) ]        ]
            [                    [ Submit → ]                        ]
            [                                                        ]
            [   Or try an example:  [Card] [Card] [Card]              ]
```

**Component hierarchy:** `SubmissionForm > (InputModeToggle, PrimaryInput, AdvancedOptionsPanel[collapsed], SubmitButton)`; `ExampleCarousel > ExampleCard[]`.

**Advanced Options Panel (expanded state):** target-framework `Select`, focus-scope `TextInput` (optional hint), human-approval-checkpoint `Toggle`, GitHub-push-destination `Select` (populated from connected GitHub App installs).

**Design tokens:** input uses `radius.lg`, `elevation.0` at rest → `elevation.1` on focus (subtle lift, ties to Document 5 §5 micro-interaction), `color.border.focus` ring.

**Error states:** inline below input, `color.status.error` text + icon, per Document 3 §2 edge cases (invalid URL, withdrawn paper, non-extractable PDF, quota exceeded, duplicate submission — each with distinct copy but identical visual treatment).

---

## Page: Job Progress

**Layout:** Full-width (not centered-card like Submission — this page has substantive content: pipeline + logs).

**Wireframe:**
```
[ Sidebar ] [ Top bar: paper title, slim progress bar beneath it     ]
            [                                                        ]
            [   ○──●──○──○──○──○   (pipeline: Doc 5 §13)             ]
            [   Extractor(done) Finder(active) Scaffolder ... Docs    ]
            [                                                        ]
            [   ┌ Current step ─────────────────────────────────┐   ]
            [   │ Finder: comparing 4 candidate repositories...  │   ]
            [   │ [Show details ▾]                               │   ]
            [   └─────────────────────────────────────────────────┘  ]
            [                                                        ]
            [   [ ▸ Live logs (collapsed) ]                          ]
            [                                                        ]
            [   [ Cancel job ]                                       ]
```

**Component hierarchy:** `PipelineVisualization > AgentNode[6]`; `CurrentStepCard`; `LiveLogPanel[collapsible]`; `HumanApprovalModal[conditional]`.

**Human Approval Modal (conditional state):** glass-morphism overlay (Document 5 §11), presents Finder's ranked candidate list as `RepoCandidateCard[]` with rationale text per card, Approve/Choose-alternative/Skip actions.

**States:** all pipeline states from Document 3 §3 (queued/running-per-agent/awaiting-approval/complete/failed/cancelled) map 1:1 to `AgentNode` visual states from Document 5 §13.

---

## Page: Job Results

**Wireframe:**
```
[ Sidebar ] [ Top bar: paper title                     [Download] [Push to GitHub] ]
            [                                                                       ]
            [  ┌─────────────┐   ┌──────────────────────────────────┐              ]
            [  │ Fidelity    │   │ Repository summary                │              ]
            [  │ Score: 87   │   │ 24 files · 1,850 LOC · 12 tests   │              ]
            [  │ (ring viz)  │   │ GPU required: yes                 │              ]
            [  └─────────────┘   └──────────────────────────────────┘              ]
            [                                                                       ]
            [  [ Open Repository Explorer ]   [ View Fidelity Report ]              ]
            [                                                                       ]
            [  ⚠ 2 assumptions were made — [view]                                   ]
            [                                                                       ]
            [  What's next: [Run locally guide] [Star on GitHub prompt]             ]
```

**Component hierarchy:** `FidelityScoreCard(ring viz, Doc 5 §9)`; `RepoSummaryCard`; `ActionBar`; `AssumptionsBanner[conditional, expandable]`; `NextStepsPanel`.

**Partial-validation state:** `RepoSummaryCard` shows per-component status chips (e.g., "Core model: ✓ validated," "Training loop: ⚠ not validated") instead of a single aggregate claim, directly implementing NFR-FID-02.

---

## Page: Job Failure / Partial Result

**Wireframe:** Similar shell to Results but headline card is `FailureSummaryCard` (specific reason + last error excerpt), with `LogsPanel` expanded by default (unlike Progress, where logs default collapsed — on a failure screen the user's next action usually requires the detail), `PartialArtifactsPanel` if any partial download exists, and `RetryActionBar` (retry / retry-with-adjusted-options / contact support).

---

## Page: Job History / Dashboard

**Layout:** Standard data-table layout with a filter/search bar above it.

**Component hierarchy:** `FilterBar(status, date-range, search-by-title)`; `JobTable > JobRow[]` (columns: paper title/thumbnail, status chip, fidelity score, date, quick-actions menu); `UsageSummaryWidget` (sidebar or top-right card showing plan usage this period); `Pagination`.

**Empty state:** replaces the table entirely with a centered `EmptyStateIllustration` + "Submit your first paper" CTA — not a table with a "no results" row, since a brand-new account should never look like a broken/empty version of the product.

---

## Page: Repository Explorer

**Layout:** Classic three-pane IDE-like layout — file tree (left, ~240px), code viewer (center, flexible), reference/annotation panel (right, ~320px, contextual — populates only when a paper-traceability annotation is active/hovered).

**Component hierarchy:** `FileTree[virtualized]`; `CodeViewer(syntax-highlighted, traceability markers inline)`; `ReferencePanel[conditional]` showing the linked paper excerpt/figure.

**Dark mode:** this page defaults to dark regardless of the user's app-wide theme setting unless explicitly overridden — matches developer-tool convention (code viewers are near-universally dark-first) and is called out here specifically since it's an intentional exception to the global theme rule.

---

## Page: Fidelity Report

**Layout:** Long-form single-column document-style layout (this page is meant to be read/shared/cited, not glanced at).

**Sections as components:** `CoverageBreakdownTable`; `StructuralChecksList`; `ExecutionValidationSummary`; `AssumptionsList[detailed, with rationale text]`; `LicenseDisclosurePanel[conditional, only if reused code present]`.

---

## Page: Workspace Settings

**Layout:** Left-nested tab navigation (Members, Billing, Integrations, Audit Log) within the main content area.

**Members tab:** `MemberTable > MemberRow[](avatar, name, role Select, remove action)`, `InviteForm`.
**Billing tab:** `PlanCard`, `UsageChart` (jobs over time, cost breakdown), `PaymentMethodPanel`.
**Integrations tab:** `GitHubAppInstallCard`, `BYOAPIKeyForm[enterprise-gated]`.
**Audit Log tab (enterprise-gated):** `AuditLogTable[virtualized, filterable]`.

---

## Page: Personal Settings

**Layout:** Simple single-column form sections: Profile, Connected Accounts, API Keys (`APIKeyTable > APIKeyRow[](name, created date, last used, revoke action)`, `GenerateKeyButton`), Notifications.

---

## Page: Public Gallery

**Layout:** Responsive card grid (`GalleryCard[]`: paper title, thumbnail/icon by domain, Fidelity Score badge, submitter handle if not anonymous), with `FilterBar(domain, sort-by-score/recency)`.

---

## Page: Shared Read-Only Job View

**Layout:** Reuses Job Results components in a read-only `ViewerContext` (action bar reduced to Download-if-enabled only), plus a small "Powered by PaperToProd — [Try it yourself]" footer CTA (GTM surface — every shared link is a funnel entry point).

---

## Cross-Page Component Library Referenced Above

`StatusChip`, `Button` (primary/secondary/ghost/destructive), `Card`, `Modal`, `Toast` (used sparingly — most confirmations are inline per Document 5's micro-interaction philosophy, Toast reserved for background/async events like "Job #123 completed" while the user is elsewhere in the app), `Table`, `Select`, `Toggle`, `TextInput`, `Tabs`, `Avatar`, `ProgressRing`, `CodeBlock`, `EmptyState`, `Skeleton` (variants matching each component's shape per Document 5 §18).

## Icons

Outline-style icon set (Lucide, per the React component library available in this environment) throughout, 20px default size in UI chrome, 16px inline-with-text, 24px for empty-state/illustrative use — single consistent icon family, never mixed with a second icon set, to preserve the "flagship product" coherence mandate.

## Error / Loading / Empty / Success States (system-wide convention)

Every data-bearing component in this document implements the same four-state contract: `loading` (skeleton, Document 5 §18 shape-matched), `empty` (illustration + actionable CTA, never a bare "no data" string), `error` (inline retry affordance, never a full-page crash unless the error is truly unrecoverable), `success`/`populated` (the designed state shown above). This contract is a build requirement for every component in the shared library, not a per-page decision.

---
*End of Document 6. Proceeding next to Document 7: Design System.*
