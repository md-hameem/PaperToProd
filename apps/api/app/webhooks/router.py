import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.auth.rbac import WorkspaceMember, WorkspaceRole
from app.database import get_db
from app.models import Webhook
from app.workspaces.router import require_workspace_role

router = APIRouter(prefix="/workspaces/{workspace_id}/webhooks", tags=["webhooks"])


class WebhookResponse(BaseModel):
    id: int
    workspace_id: int
    url: str
    secret: str
    created_at: datetime

    class Config:
        orm_mode = True


class WebhookCreateRequest(BaseModel):
    url: str


@router.get("", response_model=list[WebhookResponse])
async def list_webhooks(
    workspace_id: int,
    membership: WorkspaceMember = Depends(
        require_workspace_role([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])
    ),
    db: AsyncSession = Depends(get_db),
):
    """List all webhooks for a workspace."""
    result = await db.execute(select(Webhook).where(Webhook.workspace_id == workspace_id))
    return result.scalars().all()


@router.post("", response_model=WebhookResponse)
async def create_webhook(
    workspace_id: int,
    request: WebhookCreateRequest,
    membership: WorkspaceMember = Depends(
        require_workspace_role([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])
    ),
    db: AsyncSession = Depends(get_db),
):
    """Create a new webhook for programmatic integrations."""
    # Generate a random signing secret
    signing_secret = f"whsec_{secrets.token_hex(24)}"

    webhook = Webhook(workspace_id=workspace_id, url=request.url, secret=signing_secret)
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)

    return webhook


@router.delete("/{webhook_id}")
async def delete_webhook(
    workspace_id: int,
    webhook_id: int,
    membership: WorkspaceMember = Depends(
        require_workspace_role([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])
    ),
    db: AsyncSession = Depends(get_db),
):
    """Delete a webhook."""
    result = await db.execute(
        select(Webhook).where(Webhook.id == webhook_id, Webhook.workspace_id == workspace_id)
    )
    webhook = result.scalars().first()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    await db.delete(webhook)
    await db.commit()
    return {"status": "success"}
