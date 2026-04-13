"""Security utilities: password hashing and JWT token handling."""

import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.models import UserRole
from app.schemas import TokenPayload

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=settings.bcrypt_rounds)


def hash_password(password: str) -> str:
    """Return a bcrypt hash of the given password."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return pwd_context.verify(plain, hashed)


def hash_token(token: str) -> str:
    """Return a SHA-256 hex digest of the token (for storage)."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(user_id: UUID, role: UserRole) -> tuple[str, int]:
    """
    Create a signed JWT access token.

    Returns:
        (token_string, expires_in_seconds)
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "type": "access",
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, settings.access_token_expire_minutes * 60


def create_refresh_token(user_id: UUID, role: UserRole) -> tuple[str, datetime]:
    """
    Create a signed JWT refresh token.

    Returns:
        (token_string, expires_at datetime)
    """
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "type": "refresh",
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, expire


def decode_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT token.

    Raises:
        JWTError: if the token is invalid or expired.
    """
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    return TokenPayload(sub=payload["sub"], role=UserRole(payload["role"]), exp=payload["exp"])
