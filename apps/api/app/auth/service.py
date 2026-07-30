"""
Auth module — Business logic for authentication.
"""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuthProvider, User


async def process_oauth_callback(
    db: AsyncSession,
    provider: str,
    code: str,
    redirect_uri: str | None = None,
) -> User:
    """
    Process OAuth callback, exchange code for token, fetch user profile,
    and create/update the user in the database.
    """
    if provider not in (AuthProvider.GITHUB.value, AuthProvider.GOOGLE.value):
        raise HTTPException(status_code=400, detail="Unsupported auth provider")

    # TODO: In a real implementation, exchange the code for an access token
    # using httpx to call github/google APIs.
    # For MVP, we mock the profile fetch.

    mock_email = f"test_{code}@{provider}.com"
    mock_provider_id = f"{provider}_{code}"
    mock_display_name = f"Test User {code}"
    mock_avatar_url = f"https://api.dicebear.com/7.x/avataaars/svg?seed={code}"

    # Upsert user
    result = await db.execute(
        select(User).where(
            User.auth_provider == provider,
            User.auth_provider_id == mock_provider_id,
        )
    )
    user = result.scalars().first()

    if user:
        # Update profile
        user.email = mock_email
        user.display_name = mock_display_name
        user.avatar_url = mock_avatar_url
    else:
        # Create new
        user = User(
            email=mock_email,
            display_name=mock_display_name,
            avatar_url=mock_avatar_url,
            auth_provider=provider,
            auth_provider_id=mock_provider_id,
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    return user


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Fetch user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()
