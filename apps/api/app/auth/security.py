"""
Security utilities — JWT issuance and validation.
"""

from datetime import datetime, timedelta
from typing import Any

from jose import jwt

from app.config import settings

ALGORITHM = settings.jwt_algorithm
SECRET_KEY = settings.jwt_secret_key


def create_access_token(subject: str | int, expires_delta: timedelta | None = None) -> str:
    """Create a short-lived JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    to_encode: dict[str, Any] = {"exp": expire, "sub": str(subject)}
    encoded_jwt = str(jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM))
    return encoded_jwt


def create_refresh_token(subject: str | int, expires_delta: timedelta | None = None) -> str:
    """Create a long-lived JWT refresh token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)

    to_encode: dict[str, Any] = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = str(jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM))
    return encoded_jwt


def verify_token(token: str, is_refresh: bool = False) -> str | None:
    """Verify a JWT and return the subject (user ID) if valid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # If we expect a refresh token, ensure type matches
        if is_refresh and payload.get("type") != "refresh":
            return None

        subject: str = payload.get("sub")
        if subject is None:
            return None
        return subject
    except jwt.JWTError:
        return None
