from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


async def authenticate(db: AsyncSession, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="auth.invalid_credentials",
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="auth.account_inactive",
        )

    return user


def create_tokens(user: User) -> tuple[str, str]:
    access_token = create_access_token(str(user.id), user.role)
    refresh_token = create_refresh_token(str(user.id))
    return access_token, refresh_token


async def get_user_from_token(db: AsyncSession, token: str, token_type: str = "access") -> User:
    payload = decode_token(token)

    if payload.get("type") != token_type:
        raise HTTPException(status_code=401, detail="auth.invalid_token_type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="auth.invalid_token_payload")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="auth.user_not_found")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="auth.account_inactive")

    return user


def hash_user_password(password: str) -> str:
    return hash_password(password)
