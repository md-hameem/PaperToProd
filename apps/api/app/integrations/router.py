import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import require_workspace_role
from app.database import get_db
from app.models import Workspace, WorkspaceRole

router = APIRouter(prefix="/workspaces/{workspace_id}/integrations", tags=["Integrations"])


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

    return {"installed": bool(ws.github_installation_id), "account_name": ws.github_account_name}


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
