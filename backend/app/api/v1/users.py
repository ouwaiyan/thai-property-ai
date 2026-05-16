from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin, require_admin_or_manager
from app.dependencies import get_db
from app.models.user import User
from app.schemas import MessageResponse, PaginatedResponse
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=PaginatedResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    role: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager),
):
    items, total = await user_service.get_users(
        db, page=page, page_size=page_size, search=search, role=role, status=status
    )
    return PaginatedResponse(
        items=[UserOut.model_validate(u) for u in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total > 0 else 0,
    )


@router.post("/", response_model=UserOut, status_code=201)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = await user_service.create_user(db, body, current_user)
    return UserOut.model_validate(user)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager),
):
    user = await user_service.get_user(db, user_id)
    return UserOut.model_validate(user)


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = await user_service.update_user(db, user_id, body, current_user)
    return UserOut.model_validate(user)


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    await user_service.delete_user(db, user_id, current_user)
    return MessageResponse(message="User deactivated successfully")
