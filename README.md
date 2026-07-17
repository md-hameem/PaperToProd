# PaperToProd

**Collapse the distance between published research and working software.**

PaperToProd is a multi-agent research reproduction engine that reads an academic paper, verifies its understanding against the paper's own math and figures, checks what the community has already built, and produces code that is defensible against the source text — with every design decision traceable back to a specific section, equation, or table in the paper.

> Paste a paper. Get a repository — one that runs, that's tested, that's containerized, and that shows you exactly how each part of the code maps back to the paper.

## Current Status

🟡 **Phase 0 — Foundation & Project Setup** (In Progress)

| Milestone | Status |
|---|---|
| 0.1 Repository & Monorepo Structure | ✅ Done |
| 0.2 Development Environment | ✅ Done |
| 0.3 CI/CD Pipeline | 🔧 Partial (workflow created, image build & registry pending) |
| 0.4 Design System Foundation | ⬜ Not Started |
| 0.5 Shared Component Library | ⬜ Not Started |

See [ProjectPlanPhase.md](ProjectPlanPhase.md) for the full roadmap and task tracker.

## Architecture

```
PaperToProd/
├── apps/
│   ├── api/            → FastAPI monolith (Auth, Jobs, Billing, Integrations, Gallery)
│   ├── worker/         → Celery + LangGraph orchestration (AI agent pipeline)
│   ├── sandbox-svc/    → Isolated code execution service (gVisor/Firecracker)
│   └── web/            → Next.js frontend
│
├── packages/
│   └── shared-schemas/ → Shared Pydantic models (JobState, events)
│
├── infra/
│   ├── terraform/      → AWS infrastructure (EKS, RDS, ElastiCache, S3)
│   └── helm/           → Kubernetes Helm charts per service
│
├── golden-dataset/     → Benchmark papers for AI agent evaluation
└── Docs/               → Architecture documentation (16 specs)
```

## AI Agent Pipeline

```
┌───────────┐   ┌──────────┐   ┌────────────┐   ┌─────────┐   ┌──────────┐   ┌──────────────┐
│ Extractor │─┐ │  Finder  │   │ Scaffolder │   │  DevOps │   │ Reviewer │   │  Doc         │
│           │ ├→│          │──→│            │──→│         │──→│          │──→│  Generator   │
│ Parse     │ │ │ Search & │   │ Generate   │   │ Docker- │   │ Validate │   │  README &    │
│ paper     │─┘ │ rank     │   │ code per   │   │ ize     │   │ & repair │   │  Fidelity    │
│ structure │   │ existing │   │ component  │   │         │   │ loop     │   │  Report      │
└───────────┘   └──────────┘   └────────────┘   └─────────┘   └─────▲──┬─┘   └──────────────┘
                                                                    │  │
                                                                    └──┘
                                                              (retry on failure)
```

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js · TypeScript · Framer Motion |
| **Backend API** | FastAPI · Python 3.12 |
| **AI Orchestration** | LangGraph · Claude · OpenAI (fallback) |
| **Task Queue** | Celery · Redis |
| **Database** | PostgreSQL (async via SQLAlchemy + asyncpg) |
| **Migrations** | Alembic |
| **Vector Store** | Qdrant |
| **Object Storage** | MinIO (dev) / S3 (prod) |
| **Container Orchestration** | Kubernetes (EKS) |
| **Infrastructure** | Terraform · Helm |
| **CI/CD** | GitHub Actions |
| **Observability** | OpenTelemetry · Prometheus · Grafana |
| **Code Quality** | Ruff · mypy · pytest |

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose

### Quick Start

```bash
# Clone the repository
git clone <repo-url>
cd PaperToProd

# Copy environment variables
cp .env.example .env

# Create Python virtual environment and install dependencies
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

pip install -r apps/api/requirements.txt \
            -r apps/worker/requirements.txt \
            -r apps/sandbox-svc/requirements.txt

# Start all infrastructure services
docker compose -f docker-compose.dev.yml up -d

# Run the API server
cd apps/api
uvicorn app.main:app --reload --port 8000
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines.

## Key Concepts

| Concept | Description |
|---|---|
| **Fidelity Score** | Composite metric measuring how faithfully the generated code reproduces the paper's methodology (coverage × structural correctness × execution success) |
| **Methodology Components** | Structured breakdown of a paper's methods — each tagged with confidence level (explicit / inferred / defaulted) and source reference |
| **Repair Loop** | Reviewer agent's iterative fix cycle — diagnoses errors, routes fixes to the responsible agent (Scaffolder or DevOps), max 5 attempts |
| **Golden Dataset** | Curated benchmark papers with ground-truth annotations for evaluating agent accuracy and preventing quality regressions |
| **JobState** | Shared state object threaded through the LangGraph pipeline, checkpointed at every node transition for crash recovery |

## Documentation

Full architecture documentation lives in [`Docs/`](Docs/):

| Doc | Title |
|---|---|
| 01 | [Executive Product Vision](Docs/01-executive-product-vision.md) |
| 02 | [Software Requirements Specification](Docs/02-software-requirements-specification.md) |
| 03 | [Product Functional Specification](Docs/03-product-functional-specification.md) |
| 04 | [UX Strategy](Docs/04-ux-strategy.md) |
| 05 | [Premium Motion Design Specification](Docs/05-premium-motion-design-specification.md) |
| 06 | [Complete UI Design Specification](Docs/06-complete-ui-design-specification.md) |
| 07 | [Design System](Docs/07-design-system.md) |
| 08 | [AI Multi-Agent Architecture](Docs/08-ai-multi-agent-architecture.md) |
| 09 | [Backend Architecture](Docs/09-backend-architecture.md) |
| 10 | [Database Architecture](Docs/10-database-architecture.md) |
| 11 | [Infrastructure](Docs/11-infrastructure.md) |
| 12 | [Security Architecture](Docs/12-security-architecture.md) |
| 13 | [Testing Strategy](Docs/13-testing-strategy.md) |
| 14 | [API Specification](Docs/14-api-specification.md) |
| 15 | [Deployment Blueprint](Docs/15-deployment-blueprint.md) |
| 16 | [Engineering Roadmap](Docs/16-engineering-roadmap.md) |

## Roadmap

| Phase | Focus | Status |
|---|---|---|
| **Phase 0** | Foundation & Project Setup | 🟡 In Progress |
| **Phase 1** | MVP — Core Loop (CV papers, single-user, automatic pipeline) | ⬜ Not Started |
| **Phase 2** | V1 — Multi-Domain, Teams, Billing | ⬜ Not Started |
| **Phase 3** | V2 — Gallery, Benchmarks, Enterprise Foundations | ⬜ Not Started |
| **Phase 4** | Enterprise — On-Prem, SSO, Compliance | ⬜ Not Started |
| **Phase 5** | Future AI — Multi-paper synthesis, IDE extensions | ⬜ Not Started |

## License

Proprietary — All rights reserved.
