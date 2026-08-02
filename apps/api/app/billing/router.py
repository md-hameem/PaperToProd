from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import require_workspace_role
from app.database import get_db
from app.models import Job, SubscriptionTier, Workspace, WorkspaceRole

router = APIRouter(prefix="/workspaces/{workspace_id}/billing", tags=["Billing"])


@router.get("/usage")
async def get_usage(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(
        require_workspace_role(
            [WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.MEMBER, WorkspaceRole.BILLING]
        )
    ),
):
    """Get the current month's usage for the workspace."""
    # In MVP, we just sum up the jobs compute/token cost.
    # In a real app, we'd filter by the current billing cycle.

    stmt = select(
        func.sum(Job.compute_cost_cents).label("total_compute"),
        func.sum(Job.token_cost_cents).label("total_token"),
        func.count(Job.id).label("total_jobs"),
    ).where(Job.workspace_id == workspace_id)

    result = await db.execute(stmt)
    row = result.first()

    total_compute_cents = row.total_compute if row and row.total_compute else 0
    total_token_cents = row.total_token if row and row.total_token else 0
    total_jobs = row.total_jobs if row and row.total_jobs else 0

    # Fetch workspace to get tier
    ws_stmt = select(Workspace).where(Workspace.id == workspace_id)
    ws_result = await db.execute(ws_stmt)
    ws = ws_result.scalar_one_or_none()

    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    return {
        "workspace_id": workspace_id,
        "subscription_tier": ws.subscription_tier,
        "usage": {
            "compute_cost_cents": total_compute_cents,
            "token_cost_cents": total_token_cents,
            "total_cost_cents": total_compute_cents + total_token_cents,
            "total_jobs": total_jobs,
        },
    }


@router.post("/checkout-session")
async def create_checkout_session(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(
        require_workspace_role([WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.BILLING])
    ),
):
    """Mock endpoint to generate a Stripe checkout session."""
    ws_stmt = select(Workspace).where(Workspace.id == workspace_id)
    ws_result = await db.execute(ws_stmt)
    ws = ws_result.scalar_one_or_none()

    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if ws.subscription_tier == SubscriptionTier.PRO.value:
        raise HTTPException(status_code=400, detail="Already subscribed to PRO")

    # Return a mocked URL. In frontend, clicking this will just call the webhook mock.
    return {
        "checkout_url": f"https://mock-stripe.com/checkout/{workspace_id}",
        "workspace_id": workspace_id,
    }


# This would typically live at a root-level /webhooks/stripe endpoint, but for MVP convenience it's here
@router.post("/webhook")
async def mock_stripe_webhook(workspace_id: int, db: AsyncSession = Depends(get_db)):
    """Mock endpoint to simulate a successful Stripe payment."""
    ws_stmt = select(Workspace).where(Workspace.id == workspace_id)
    ws_result = await db.execute(ws_stmt)
    ws = ws_result.scalar_one_or_none()

    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    ws.subscription_tier = SubscriptionTier.PRO.value
    ws.stripe_customer_id = f"cus_mock_{workspace_id}"
    ws.stripe_subscription_id = f"sub_mock_{workspace_id}"

    await db.commit()
    return {"status": "success", "tier": ws.subscription_tier}
