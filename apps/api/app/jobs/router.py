"""
Jobs module — API routes for job lifecycle (create, list, get, cancel, approve, artifacts).
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def jobs_health():
    return {"status": "ok", "module": "jobs"}


# TODO: POST /jobs, GET /jobs, GET /jobs/{id}, POST /jobs/{id}/cancel,
#       POST /jobs/{id}/approve, GET /jobs/{id}/logs,
#       GET /jobs/{id}/artifacts/repository, POST /jobs/{id}/artifacts/push-to-github,
#       GET /jobs/{id}/fidelity-report
