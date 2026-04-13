"""Auth and token routes."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import RefreshToken, User
from app.schemas import LoginRequest, RefreshRequest, TokenResponse, TokenVerifyResponse
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Authenticate a user and return access + refresh tokens."""
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    access_token, expires_in = create_access_token(user.id, user.role)
    refresh_token_str, refresh_expires = create_refresh_token(user.id, user.role)

    db_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token_str),
        expires_at=refresh_expires,
    )
    db.add(db_token)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        expires_in=expires_in,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Exchange a valid refresh token for a new token pair."""
    from jose import JWTError

    try:
        token_data = decode_token(payload.refresh_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    token_hash = hash_token(payload.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked.is_(False),
        )
    )
    db_token = result.scalar_one_or_none()
    if not db_token or db_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or revoked")

    # Rotate: revoke old token
    db_token.revoked = True

    result = await db.execute(select(User).where(User.id == db_token.user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found or disabled")

    access_token, expires_in = create_access_token(user.id, user.role)
    new_refresh_str, new_expires = create_refresh_token(user.id, user.role)

    new_db_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(new_refresh_str),
        expires_at=new_expires,
    )
    db.add(new_db_token)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_str,
        expires_in=expires_in,
    )


@router.post("/logout")
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> dict:
    """Revoke a refresh token (logout)."""
    token_hash = hash_token(payload.refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    db_token = result.scalar_one_or_none()
    if db_token:
        db_token.revoked = True
        await db.commit()
    return {"detail": "Logged out"}


@router.post("/verify", response_model=TokenVerifyResponse)
async def verify_token(authorization: str = Header(default="")) -> TokenVerifyResponse:
    """
    Service-to-service endpoint: verify an access token.
    Pass the token in the standard Authorization header: Bearer <token>
    """
    from jose import JWTError

    if not authorization.startswith("Bearer "):
        return TokenVerifyResponse(valid=False)
    token = authorization.removeprefix("Bearer ")
    try:
        payload = decode_token(token)
        return TokenVerifyResponse(valid=True, user_id=payload.sub, role=payload.role)
    except JWTError:
        return TokenVerifyResponse(valid=False)
