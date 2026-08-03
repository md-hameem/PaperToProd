import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import require_workspace_role
from app.database import get_db
from app.models import SubscriptionTier, Workspace, WorkspaceRole
from app.utils.crypto import encrypt_key

router = APIRouter(prefix="/workspaces/{workspace_id}/integrations", tags=["Integrations"])


class BYOKeyRequest(BaseModel):
    provider: str
    api_key: str


@router.get("/github")
async def get_github_integration(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(
        require_workspace_role([WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.MEMBER])
    ),
):
    """Get the current GitHub integration status."""
    ws_stmt = select(Workspace).where(Workspace.id == workspace_id)
    ws_result = await db.execute(ws_stmt)
    ws = ws_result.scalar_one_or_none()

    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    return {
        "github": {
            "installed": bool(ws.github_installation_id),
            "account_name": ws.github_account_name,
        },
        "byo_llm": {"has_key": bool(ws.byo_llm_api_key_encrypted), "provider": ws.byo_llm_provider},
    }


@router.post("/github/install")
async def mock_install_github(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_workspace_role([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])),
):
    """
    Mock endpoint for installing GitHub App.
    In a real app, this might redirect to GitHub or process an OAuth callback.
    Here, it simply sets a mocked installation ID on the workspace.
    """
    ws_stmt = select(Workspace).where(Workspace.id == workspace_id)
    ws_result = await db.execute(ws_stmt)
    ws = ws_result.scalar_one_or_none()

    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    ws.github_installation_id = f"inst_{uuid.uuid4().hex[:8]}"
    ws.github_account_name = f"{ws.name.lower().replace(' ', '-')}-org"

    await db.commit()

    return {
        "status": "success",
        "installation_id": ws.github_installation_id,
        "account_name": ws.github_account_name,
    }


@router.delete("/github")
async def disconnect_github(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_workspace_role([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])),
):
    """Disconnect GitHub from the workspace."""
    ws_stmt = select(Workspace).where(Workspace.id == workspace_id)
    ws_result = await db.execute(ws_stmt)
    ws = ws_result.scalar_one_or_none()

    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    ws.github_installation_id = None
    ws.github_account_name = None

    await db.commit()

    return {"status": "success"}


@router.post("/byo-key")
async def add_byo_llm_key(
    workspace_id: int,
    payload: BYOKeyRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_workspace_role([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])),
):
    """Add a Bring-Your-Own LLM API Key (Enterprise only)."""
    ws_stmt = select(Workspace).where(Workspace.id == workspace_id)
    ws_result = await db.execute(ws_stmt)
    ws = ws_result.scalar_one_or_none()

    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if ws.subscription_tier != SubscriptionTier.ENTERPRISE:
        raise HTTPException(
            status_code=403, detail="BYO LLM keys require an Enterprise subscription"
        )

    if payload.provider not in ["openai", "anthropic"]:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    # Encrypt key for at-rest storage
    ws.byo_llm_provider = payload.provider
    ws.byo_llm_api_key_encrypted = encrypt_key(payload.api_key)

    await db.commit()

    return {"status": "success"}


@router.delete("/byo-key")
async def remove_byo_llm_key(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_workspace_role([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])),
):
    """Remove the BYO LLM API Key."""
    ws_stmt = select(Workspace).where(Workspace.id == workspace_id)
    ws_result = await db.execute(ws_stmt)
    ws = ws_result.scalar_one_or_none()

    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    ws.byo_llm_provider = None
    ws.byo_llm_api_key_encrypted = None

    await db.commit()

    return {"status": "success"}
