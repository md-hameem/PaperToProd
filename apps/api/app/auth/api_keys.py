import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import get_current_user
from app.database import get_db
from app.models import ApiKey, User

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


class ApiKeyCreateRequest(BaseModel):
    name: str


class ApiKeyCreateResponse(BaseModel):
    id: int
    name: str
    raw_key: str  # Only returned once!


class ApiKeySummaryResponse(BaseModel):
    id: int
    name: str
    prefix: str
    created_at: str


def _generate_api_key() -> tuple[str, str, str]:
    """Generates a raw key, its hash, and prefix."""
    raw_key = f"ptp_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    prefix = raw_key[:7]
    return raw_key, key_hash, prefix


@router.post("", response_model=ApiKeyCreateResponse)
async def create_api_key(
    payload: ApiKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key for the authenticated user."""
    raw_key, key_hash, prefix = _generate_api_key()

    new_key = ApiKey(
        user_id=current_user.id,
        name=payload.name,
        key_hash=key_hash,
        prefix=prefix,
    )
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)

    return ApiKeyCreateResponse(id=new_key.id, name=new_key.name, raw_key=raw_key)


@router.get("", response_model=list[ApiKeySummaryResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys for the authenticated user."""
    stmt = (
        select(ApiKey).where(ApiKey.user_id == current_user.id).order_by(ApiKey.created_at.desc())
    )
    result = await db.execute(stmt)
    keys = result.scalars().all()

    return [
        ApiKeySummaryResponse(
            id=k.id,
            name=k.name,
            prefix=k.prefix,
            created_at=k.created_at.isoformat(),
        )
        for k in keys
    ]


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an API key."""
    stmt = select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
    result = await db.execute(stmt)
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    await db.delete(key)
    await db.commit()
    return {"status": "revoked"}
