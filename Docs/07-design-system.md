# PaperToProd — Document 7: Design System

**Status:** Draft v1.0
**Format note:** Values below are expressed as design tokens (Figma Variables-compatible naming: `category/property/variant`) so they map directly into a Figma library and a CSS custom-properties / Tailwind config implementation without translation loss.

---

## 1. Color Palette

**Philosophy:** A near-monochrome, dark-first neutral base (matching Linear/Vercel/Arc positioning) with a single confident accent used sparingly, plus a small functional-status set. No decorative secondary/tertiary brand colors — restraint is the brand signal.

### Neutrals (base UI)
| Token | Dark mode value | Light mode value | Usage |
|---|---|---|---|
| `color/surface/base` | #0A0A0C | #FFFFFF | App background |
| `color/surface/raised` | #131316 | #F7F7F8 | Cards, panels |
| `color/surface/overlay` | rgba(19,19,22,0.72) + blur | rgba(255,255,255,0.72) + blur | Modals, glass surfaces (Doc 5 §11) |
| `color/border/default` | #26262B | #E5E5E8 | Dividers, card borders |
| `color/border/focus` | #7C6CF0 | #6E5AE0 | Focus rings (also `color/accent/primary`) |
| `color/text/primary` | #F2F2F3 | #14141A | Headlines, body |
| `color/text/secondary` | #A0A0A8 | #5C5C66 | Supporting text |
| `color/text/tertiary` | #6B6B74 | #8A8A92 | Placeholder, disabled |

### Accent
| Token | Value | Usage |
|---|---|---|
| `color/accent/primary` | #7C6CF0 (dark) / #6E5AE0 (light) | Primary CTAs, active states, focus rings, the pipeline "active" glow |
| `color/accent/primary-subtle` | 12% opacity of primary | Selected-row backgrounds, subtle highlights |

### Status (functional — never used decoratively, always tied to a real state)
| Token | Value | Usage |
|---|---|---|
| `color/status/success` | #3DD68C | Fidelity high band, validated chip, complete node |
| `color/status/warning` | #F5A623 | Partial validation, retry/repair state, assumptions banner |
| `color/status/error` | #F0554C | Failed job, field errors |
| `color/status/info` | #5AA9F5 | Neutral informational banners |

### Agent Accent Set (pipeline visualization only, Doc 5 §13)
Six distinct low-saturation hues (one per agent) derived from the primary accent's hue family via consistent lightness/saturation offsets — not arbitrary rainbow colors — so the pipeline reads as "one coherent system with six roles," not six unrelated brand colors: `color/agent/extractor`, `/finder`, `/scaffolder`, `/devops`, `/reviewer`, `/documenter`.

## 2. Typography Scale

**Typeface:** A single geometric/grotesk sans for UI (e.g., Inter or a comparable variable font) + a monospace face for all code/terminal surfaces (e.g., JetBrains Mono). Two-font system only.

| Token | Size / Line-height | Weight | Usage |
|---|---|---|---|
| `type/display` | 48px / 56px | 600 | Landing hero headline only |
| `type/heading-1` | 32px / 40px | 600 | Page titles |
| `type/heading-2` | 24px / 32px | 600 | Section headers |
| `type/heading-3` | 18px / 26px | 600 | Card headers |
| `type/body-lg` | 16px / 24px | 400 | Primary body text |
| `type/body-sm` | 14px / 20px | 400 | Secondary/dense UI text |
| `type/caption` | 12px / 16px | 500 | Labels, chips, metadata |
| `type/mono` | 14px / 22px | 400 | Code, logs, terminal |

## 3. Spacing Scale

Base unit 4px, exponential-friendly progression: `spacing/1`=4, `/2`=8, `/3`=12, `/4`=16, `/6`=24, `/8`=32, `/12`=48, `/16`=64, `/24`=96 (px). All component padding/margins reference these tokens exclusively — no arbitrary pixel values permitted in implementation.

## 4. Elevation

Three-tier shadow system (paired with the glass-morphism rules in Document 5 §11):

| Token | Shadow | Usage |
|---|---|---|
| `elevation/0` | none | Resting flat surfaces |
| `elevation/1` | `0 1px 2px rgba(0,0,0,0.24), 0 1px 1px rgba(0,0,0,0.12)` | Cards at rest, top bar |
| `elevation/2` | `0 4px 12px rgba(0,0,0,0.32)` | Hovered cards, dropdowns |
| `elevation/3` | `0 16px 40px rgba(0,0,0,0.40)` | Modals, command palette |

## 5. Corner Radius

| Token | Value | Usage |
|---|---|---|
| `radius/sm` | 6px | Chips, small buttons |
| `radius/md` | 10px | Inputs, standard buttons |
| `radius/lg` | 16px | Cards, panels |
| `radius/xl` | 24px | Modals, the primary Submission input (per Doc 6, deliberately more rounded to feel inviting/focal) |
| `radius/full` | 9999px | Avatars, status dots |

## 6. Shadow System

See Elevation (§4) — shadows are always paired 1:1 with elevation tokens; no ad hoc shadow values permitted, ensuring the "depth" cues referenced throughout Document 5 remain a coherent, finite system.

## 7. Animation Tokens

Directly reused from Document 5 to keep motion and static design systems in lockstep (single source of truth, no duplication of values):

| Token | Value |
|---|---|
| `motion/duration/micro` | 120ms |
| `motion/duration/component` | 250ms |
| `motion/duration/system` | 450ms |
| `motion/duration/screen` | 300ms |
| `motion/spring/snappy` | stiffness 500, damping 30 |
| `motion/spring/settle` | stiffness 220, damping 24 |
| `motion/spring/pipeline` | stiffness 180, damping 20 |
| `motion/spring/celebration` | stiffness 260, damping 16 |

## 8. Grid

12-column grid, `spacing/6` (24px) gutters, max content width 1280px for dashboard/settings pages; Submission/Progress/Results pages use a narrower centered 8-column max-width (960px) reading measure appropriate to their document/focus-style content (per Document 6).

## 9. Breakpoints

| Token | Value | Notes |
|---|---|---|
| `breakpoint/sm` | 480px | Mobile |
| `breakpoint/md` | 768px | Tablet / sidebar collapse threshold |
| `breakpoint/lg` | 1024px | Small desktop |
| `breakpoint/xl` | 1280px | Standard desktop, max content width |

## 10. Components (library inventory, states per Document 6 §"Cross-Page Component Library")

Each component ships in Figma with variants for: default/hover/focus/active/disabled, and where applicable loading/empty/error/success per the four-state contract (Document 6). Inventory: `Button` (4 variants × 5 states), `Input`, `Select`, `Toggle`, `Checkbox`, `Card`, `Modal`, `Toast`, `Tabs`, `Table` + `TableRow`, `StatusChip` (6 semantic colors max, mapped to `color/status/*` and `color/agent/*` only — never arbitrary colors per-instance), `Avatar`, `ProgressRing`, `ProgressBar`, `CodeBlock`, `Skeleton`, `EmptyState`, `AgentNode` (pipeline-specific, Document 5 §13), `FidelityScoreCard`.

## 11. Icons

Single icon family (Lucide-derived, per Document 6 §Icons), 20/16/24px sizing tokens (`icon/sm`=16, `icon/md`=20, `icon/lg`=24), stroke width 1.5px fixed across all sizes for visual consistency.

## 12. Illustrations

A small set of custom line-art empty-state illustrations (monochrome, using `color/text/tertiary` + `color/accent/primary` accent strokes only — never full-color illustration, keeping the restrained brand palette intact even in illustrative moments): "no jobs yet," "job failed," "empty gallery," "no team members."

## 13. 3D Assets

Single hero asset (Document 5 §12's abstract paper→graph form), authored once in Blender or directly as procedural Three.js geometry, exported/optimized for R3F. No additional 3D assets required elsewhere per the "3D is marketing-only" rule (Document 5 §12).

## 14. Accessibility Tokens

| Token | Value | Note |
|---|---|---|
| `a11y/contrast/min-text` | 4.5:1 | WCAG AA body text minimum, enforced against `color/text/*` vs `color/surface/*` pairs |
| `a11y/contrast/min-large-text` | 3:1 | Headings ≥24px |
| `a11y/focus-ring/width` | 2px | Consistent with `color/border/focus` |
| `a11y/motion/reduced` | boolean flag | Gates all `motion/spring/*` and ambient animations per Document 5's `prefers-reduced-motion` rule |

## 15. Component States

Standard 5-state matrix (default/hover/focus/active/disabled) applied uniformly; interactive components additionally define pressed and loading sub-states where relevant (primarily `Button`, `Input`). This matrix is enforced as a Figma component-variant requirement, not left to per-designer discretion.

## 16. Naming Convention

`category/property/variant` (e.g., `color/status/success`, `spacing/4`, `motion/spring/pipeline`) — chosen to map 1:1 onto both Figma Variables' grouping syntax and CSS custom property naming (`--color-status-success`), so design and implementation tokens never drift into two parallel naming schemes.

## 17. Design Tokens / Figma Variables

All tokens in this document are defined as Figma Variables under matching collections (`Color`, `Typography`, `Spacing`, `Elevation`, `Radius`, `Motion`, `Breakpoint`, `Accessibility`), with a `Dark`/`Light` mode pair on the `Color` collection specifically (all other collections are mode-independent). Engineering consumes the same tokens via a generated `tokens.json` → Tailwind theme extension, ensuring design and code never hand-maintain two copies of the same values (a common source of visual drift this system is explicitly designed to prevent).

---
*End of Document 7. Proceeding next to Document 8: AI Multi-Agent Architecture.*
