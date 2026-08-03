from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import Notification, User

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    id: int
    message: str
    type: str
    is_read: bool
    created_at: datetime
    read_at: datetime | None

    class Config:
        orm_mode = True


@router.get("", response_model=list[NotificationResponse])
async def get_notifications(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get all notifications for the current user."""
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )
    return result.scalars().all()


@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a specific notification as read."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == current_user.id
        )
    )
    notification = result.scalars().first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    notification.read_at = datetime.utcnow()
    await db.commit()

    return {"status": "success"}


@router.post("/mock-trigger")
async def mock_trigger_notification(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Test endpoint to trigger a mock notification."""
    notif = Notification(
        user_id=current_user.id,
        message="Your Job #102 has successfully completed!",
        type="job_complete",
    )
    db.add(notif)
    await db.commit()
    return {"status": "success"}
