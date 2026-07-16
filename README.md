# PaperToProd

**Collapse the distance between published research and working software.**

PaperToProd is a multi-agent research reproduction engine that reads an academic paper, verifies its understanding against the paper's own math and figures, checks what the community has already built, and produces code that is defensible against the source text — with every design decision traceable back to a specific section, equation, or table in the paper.

> Paste a paper. Get a repository — one that runs, that's tested, that's containerized, and that shows you exactly how each part of the code maps back to the paper.

## Architecture

```
apps/
  api/          → FastAPI monolith (Auth, Jobs, Billing, Integrations, Gallery)
  worker/       → Celery + LangGraph orchestration (AI agent pipeline)
  sandbox-svc/  → Isolated code execution service (gVisor/Firecracker)
  web/          → Next.js frontend

packages/
  shared-schemas/  → Shared Pydantic models (JobState, events, etc.)

infra/
  terraform/    → AWS infrastructure (EKS, RDS, ElastiCache, S3)
  helm/         → Kubernetes Helm charts per service
```

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, TypeScript, Framer Motion |
| Backend API | FastAPI (Python) |
| AI Orchestration | LangGraph, Claude/OpenAI |
| Task Queue | Celery + Redis |
| Database | PostgreSQL |
| Vector Store | Qdrant |
| Object Storage | MinIO / S3 |
| Container Orchestration | Kubernetes (EKS) |
| CI/CD | GitHub Actions |

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose

### Development Setup

```bash
# Clone the repository
git clone <repo-url>
cd PaperToProd

# Copy environment variables
cp .env.example .env

# Start all services
docker compose -f docker-compose.dev.yml up -d

# API setup
cd apps/api
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Frontend setup
cd apps/web
npm install
npm run dev
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines.

## Documentation

Full architecture documentation lives in [`Docs/`](Docs/):

| Doc | Title |
|---|---|
| 01 | Executive Product Vision |
| 02 | Software Requirements Specification |
| 03 | Product Functional Specification |
| 04 | UX Strategy |
| 05 | Premium Motion Design Specification |
| 06 | Complete UI Design Specification |
| 07 | Design System |
| 08 | AI Multi-Agent Architecture |
| 09 | Backend Architecture |
| 10 | Database Architecture |
| 11 | Infrastructure |
| 12 | Security Architecture |
| 13 | Testing Strategy |
| 14 | API Specification |
| 15 | Deployment Blueprint |
| 16 | Engineering Roadmap |

## License

Proprietary — All rights reserved.
