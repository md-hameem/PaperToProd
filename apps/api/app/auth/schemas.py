"""
Auth module — API request/response schemas.
"""

from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Response returned upon successful authentication/token refresh."""

    access_token: str
    token_type: str = "bearer"


class AuthCallbackRequest(BaseModel):
    """Data sent by frontend after completing OAuth flow."""

    provider: str
    code: str
    redirect_uri: str | None = None


class UserProfileResponse(BaseModel):
    """Response containing user profile info."""

    id: int
    email: str
    display_name: str | None
    avatar_url: str | None
    auth_provider: str

    model_config = {"from_attributes": True}
