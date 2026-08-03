import hashlib
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import get_current_user
from app.database import get_db
from app.models import ApiKey, User

router = APIRouter(prefix="/users/me", tags=["Users"])


class UserProfileUpdate(BaseModel):
    display_name: str | None = None
    email: str | None = None
    notification_preferences: dict | None = None


class ApiKeyCreate(BaseModel):
    name: str


class ApiKeyResponse(BaseModel):
    id: int
    name: str
    prefix: str
    created_at: datetime
    last_used_at: datetime | None


class ApiKeyCreateResponse(ApiKeyResponse):
    key: str  # Only returned once!


@router.get("", response_model=dict)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "avatar_url": current_user.avatar_url,
        "notification_preferences": current_user.notification_preferences,
    }


@router.patch("", response_model=dict)
async def update_me(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user profile."""
    if payload.display_name is not None:
        current_user.display_name = payload.display_name
    if payload.email is not None:
        current_user.email = payload.email
    if payload.notification_preferences is not None:
        current_user.notification_preferences = payload.notification_preferences

    await db.commit()
    return {
        "id": current_user.id,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "avatar_url": current_user.avatar_url,
        "notification_preferences": current_user.notification_preferences,
    }


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active API keys for the current user."""
    stmt = (
        select(ApiKey).where(ApiKey.user_id == current_user.id).order_by(ApiKey.created_at.desc())
    )
    result = await db.execute(stmt)
    keys = result.scalars().all()

    return [
        {
            "id": k.id,
            "name": k.name,
            "prefix": k.prefix,
            "created_at": k.created_at,
            "last_used_at": k.last_used_at,
        }
        for k in keys
    ]


@router.post("/api-keys", response_model=ApiKeyCreateResponse)
async def create_api_key(
    payload: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new API key. The raw key is returned exactly once."""
    raw_key = f"ptp_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    prefix = raw_key[:10]  # ptp_XXXXXX

    api_key = ApiKey(user_id=current_user.id, name=payload.name, key_hash=key_hash, prefix=prefix)
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return {
        "id": api_key.id,
        "name": api_key.name,
        "prefix": api_key.prefix,
        "created_at": api_key.created_at,
        "last_used_at": api_key.last_used_at,
        "key": raw_key,
    }


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an API key."""
    stmt = select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    await db.delete(api_key)
    await db.commit()
    return None
