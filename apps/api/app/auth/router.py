"""
Auth module — API routes for authentication and OAuth callbacks.
"""

from datetime import UTC

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import security, service
from app.auth.schemas import AuthCallbackRequest, TokenResponse
from app.database import get_db
from app.models import User

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency to get the current authenticated user from JWT or API Key."""

    if token.startswith("ptp_"):
        import hashlib

        from sqlalchemy import select

        from app.models import ApiKey

        # API Key authentication
        key_hash = hashlib.sha256(token.encode()).hexdigest()
        stmt = select(ApiKey).where(ApiKey.key_hash == key_hash)
        result = await db.execute(stmt)
        api_key = result.scalar_one_or_none()

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Update last_used_at (optional optimization: don't await/commit on every request or do it async)
        from datetime import datetime

        api_key.last_used_at = datetime.now(UTC)
        await db.commit()

        user = await service.get_user_by_id(db, api_key.user_id)
    else:
        # JWT authentication
        user_id = security.verify_token(token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = await service.get_user_by_id(db, int(user_id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/callback", response_model=TokenResponse)
async def oauth_callback(
    request: AuthCallbackRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Handle OAuth callback, exchange code for user profile, issue tokens."""
    user = await service.process_oauth_callback(
        db=db,
        provider=request.provider,
        code=request.code,
        redirect_uri=request.redirect_uri,
    )

    # Issue tokens
    access_token = security.create_access_token(subject=user.id)
    refresh_token = security.create_refresh_token(subject=user.id)

    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 days
    )

    return TokenResponse(access_token=access_token)


@router.get("/health")
async def auth_health():
    return {"status": "ok", "module": "auth"}
