"""
Auth module — API routes for authentication & OAuth flows.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def auth_health():
    return {"status": "ok", "module": "auth"}


# TODO: Implement OAuth flows (GitHub, Google), JWT issuance, refresh token
