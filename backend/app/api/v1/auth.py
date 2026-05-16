from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.dependencies import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UserMe
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate(db, body.email, body.password)
    access_token, refresh_token = auth_service.create_tokens(user)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.get_user_from_token(db, body.refresh_token, token_type="refresh")
    access_token, refresh_token = auth_service.create_tokens(user)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserMe)
async def me(current_user: User = Depends(get_current_user)):
    return UserMe(
        id=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Logged out successfully"}
