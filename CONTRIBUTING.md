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

3. **Start infrastructure services:**
   ```bash
   docker compose -f docker-compose.dev.yml up -d postgres redis qdrant minio
   ```

4. **Set up the API:**
   ```bash
   cd apps/api
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

5. **Set up the frontend (once initialized):**
   ```bash
   cd apps/web
   npm install
   npm run dev
   ```

## Project Structure

```
PaperToProd/
├── apps/
│   ├── api/            # FastAPI monolith (Auth, Jobs, Billing, etc.)
│   ├── worker/         # Celery + LangGraph AI agent pipeline
│   ├── sandbox-svc/    # Isolated code execution service
│   └── web/            # Next.js frontend
├── packages/
│   └── shared-schemas/ # Shared Pydantic models (JobState, events)
├── infra/
│   ├── terraform/      # AWS infrastructure
│   └── helm/           # Kubernetes Helm charts
├── golden-dataset/     # Benchmark papers for AI evaluation
├── Docs/               # Architecture documentation (16 docs)
└── docker-compose.dev.yml
```

## Code Standards

### Python (apps/api, apps/worker, apps/sandbox-svc)
- **Formatter:** Ruff / Black
- **Linter:** Ruff
- **Type checker:** mypy
- **Test runner:** pytest
- **Style:** Follow existing module structure (router → service → models → schemas)

### TypeScript (apps/web)
- **Linter:** ESLint
- **Formatter:** Prettier
- **Style:** TypeScript strict mode, functional components, Framer Motion for animation

### Commit Messages
Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

### Pull Requests
- All PRs require passing CI (lint, typecheck, tests)
- Agent/prompt changes additionally require Golden Dataset regression gate pass
- Code review required before merge

## Architecture Documentation
Full specs are in `Docs/` (Documents 01–16). Read the relevant docs before working on a module.
