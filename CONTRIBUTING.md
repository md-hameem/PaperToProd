# Contributing to PaperToProd

## Development Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- Git

### Getting Started

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd PaperToProd
   ```

2. **Copy environment variables:**
   ```bash
   cp .env.example .env
   ```

3. **Set up Python environment:**
   ```bash
   python -m venv .venv

   # Windows
   .venv\Scripts\activate

   # Linux/Mac
   source .venv/bin/activate

   # Install all service dependencies
   pip install -r apps/api/requirements.txt \
               -r apps/worker/requirements.txt \
               -r apps/sandbox-svc/requirements.txt
   ```

4. **Install pre-commit hooks:**
   ```bash
   pip install pre-commit
   pre-commit install
   ```
   This installs **10 hooks** that run on every commit:
   - Ruff lint + auto-fix
   - Ruff format
   - mypy type checking
   - Trailing whitespace removal
   - End-of-file fixer
   - YAML/JSON syntax validation
   - Large file check (500KB max)
   - Merge conflict detection
   - Private key detection

5. **Start infrastructure services:**
   ```bash
   docker compose -f docker-compose.dev.yml up -d postgres redis qdrant minio
   ```

6. **Run the API server:**
   ```bash
   cd apps/api
   uvicorn app.main:app --reload --port 8000
   ```

7. **Set up and run the frontend:**
   ```bash
   cd apps/web
   npm install
   npm run dev
   ```
   The dev server starts at `http://localhost:3000`.

## Project Structure

```
PaperToProd/
├── apps/
│   ├── api/                # FastAPI monolith (Auth, Jobs, Billing, etc.)
│   │   ├── app/
│   │   │   ├── main.py       # Application entry point
│   │   │   ├── config.py     # Pydantic settings
│   │   │   ├── database.py   # Async SQLAlchemy session management
│   │   │   ├── routers/      # API route handlers
│   │   │   ├── services/     # Business logic layer
│   │   │   ├── models/       # SQLAlchemy ORM models
│   │   │   └── schemas/      # Pydantic request/response schemas
│   │   └── requirements.txt
│   │
│   ├── worker/             # Celery + LangGraph AI agent pipeline
│   │   ├── agents/           # Individual AI agent implementations
│   │   ├── graph/            # LangGraph pipeline definition
│   │   └── requirements.txt
│   │
│   ├── sandbox-svc/        # Isolated code execution service
│   │   ├── runner/           # Execution environment management
│   │   └── requirements.txt
│   │
│   └── web/                # Next.js 16 frontend
│       ├── src/
│       │   ├── app/            # Next.js App Router pages
│       │   ├── components/
│       │   │   └── ui/         # Shared component library (8 components)
│       │   ├── lib/            # Utilities (motion presets, helpers)
│       │   ├── providers/      # React context providers (theme)
│       │   └── styles/         # Design tokens (CSS custom properties)
│       └── package.json
│
├── packages/
│   └── shared-schemas/     # Shared Pydantic models (JobState, events)
│       └── shared_schemas/
│           ├── job_state.py   # Central pipeline state model
│           └── events.py      # WebSocket event types
│
├── infra/
│   ├── terraform/          # AWS infrastructure (EKS, RDS, etc.)
│   └── helm/               # Kubernetes Helm charts
│
├── golden-dataset/         # Benchmark papers for AI evaluation
├── Docs/                   # Architecture documentation (16 specs)
├── .pre-commit-config.yaml # Pre-commit hook configuration
├── pyproject.toml          # Python tooling config (Ruff, mypy, pytest)
├── docker-compose.dev.yml  # Local development service topology
└── ProjectPlanPhase.md     # Phase-by-phase development tracker
```

## Code Standards

### Python (apps/api, apps/worker, apps/sandbox-svc)

- **Formatter & Linter:** [Ruff](https://docs.astral.sh/ruff/) — configured in `pyproject.toml`
- **Type checker:** [mypy](https://mypy.readthedocs.io/) — strict mode, also via `pyproject.toml`
- **Test runner:** pytest
- **Style:** Follow the existing module structure: `routers/` → `services/` → `models/` → `schemas/`
- **Python version:** 3.12+ — use modern syntax: `str | None` instead of `Optional[str]`, `StrEnum` instead of `str, Enum`

Run checks manually:
```bash
# Lint
.venv/Scripts/ruff check apps/ packages/

# Format
.venv/Scripts/ruff format apps/ packages/

# Type check
.venv/Scripts/mypy apps/ --config-file pyproject.toml
```

### TypeScript / React (apps/web)

- **Framework:** Next.js 16 (App Router, Turbopack)
- **Linter:** ESLint (`eslint-config-next`)
- **Styling:** CSS Modules (`*.module.css`) — reference design tokens from `src/styles/tokens.css`
- **Animation:** Framer Motion — use spring presets from `src/lib/motion.ts`
- **Icons:** Lucide React
- **Theme:** Dark mode default — use `useTheme()` from `src/providers/theme-provider.tsx`
- **Components:** All shared UI lives in `src/components/ui/` — import via `@/components/ui`

Run checks:
```bash
cd apps/web

# Lint
npx eslint .

# Type check
npx tsc --noEmit

# Build (validates everything)
npx next build
```

### Component Conventions

When creating new UI components:

1. **Directory structure:** `src/components/ui/ComponentName/`
   - `ComponentName.tsx` — Component implementation
   - `ComponentName.module.css` — Styles using design tokens
   - `index.ts` — Barrel export
2. **Use design tokens:** All colors, spacing, radii, and transitions must reference CSS custom properties from `tokens.css` — never hard-code values.
3. **Use `"use client"` directive** for any component that uses hooks, event handlers, or Framer Motion.
4. **Export from barrel:** Add your component to `src/components/ui/index.ts`.

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | When to use |
|---|---|
| `feat:` | New feature or component |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `refactor:` | Code change with no functional difference |
| `test:` | Adding or updating tests |
| `chore:` | Tooling, config, dependency updates |
| `style:` | Formatting, whitespace (no logic change) |

Examples:
```
feat: add Toast notification component with auto-dismiss
fix: resolve ProgressRing SVG rendering on Safari
docs: update Phase 1 status in ProjectPlanPhase.md
chore: upgrade framer-motion to v12
```

### Pull Requests

- All PRs require passing CI (lint, typecheck, tests)
- Agent/prompt changes additionally require Golden Dataset regression gate pass
- Code review required before merge
- Keep PRs focused — one feature or fix per PR

## Architecture Documentation

Full specs are in `Docs/` (Documents 01–16). **Read the relevant docs before working on a module:**

| Area | Key Docs |
|---|---|
| UI / Frontend | Doc 04 (UX), Doc 05 (Motion), Doc 06 (UI), Doc 07 (Design System) |
| AI Agents | Doc 08 (Multi-Agent Architecture) |
| Backend | Doc 09 (Backend), Doc 10 (Database), Doc 14 (API Spec) |
| Infrastructure | Doc 11 (Infra), Doc 15 (Deployment) |
| Quality | Doc 12 (Security), Doc 13 (Testing) |

## Troubleshooting

### Pre-commit hooks failing on commit

If `ruff format` auto-fixes files, the commit will be blocked. Just re-run `git add -A && git commit` — the formatted files will pass on the second attempt.

### mypy errors in pre-commit

mypy runs with `--ignore-missing-imports` in pre-commit. If you see import errors for third-party libraries, ensure they're listed in the `additional_dependencies` section of `.pre-commit-config.yaml`.

### Next.js build fails

Run `npx next build` locally to see TypeScript errors. Common issues:
- Framer Motion `onDrag` type conflicts — avoid spreading `React.HTMLAttributes` onto `motion.*` elements
- Use `as const` on spring transition configs to get literal types
