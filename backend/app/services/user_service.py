from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services import auth_service as auth_svc
from app.services.audit_service import log as audit_log


async def get_users(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    role: str | None = None,
    status: str | None = None,
) -> tuple[list[User], int]:
    query = select(User)
    count_query = select(func.count(User.id))

    if search:
        filter_expr = or_(
            User.name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%"),
        )
        query = query.where(filter_expr)
        count_query = count_query.where(filter_expr)
    if role:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)
    if status:
        query = query.where(User.status == status)
        count_query = count_query.where(User.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    items = list(result.scalars().all())

    return items, total


async def get_user(db: AsyncSession, user_id: UUID) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user.not_found")
    return user


async def create_user(db: AsyncSession, data: UserCreate, current_user: User) -> User:
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="user.email_registered",
        )

    from app.utils.security import validate_password_strength
    valid, err_msg = validate_password_strength(data.password)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    user = User(
        name=data.name,
        email=data.email,
        password_hash=auth_svc.hash_user_password(data.password),
        role=data.role,
        status="active",
    )
    db.add(user)
    await db.flush()

    await audit_log(
        db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="user",
        entity_id=user.id,
        after_json={"name": user.name, "email": user.email, "role": user.role},
    )

    return user


async def update_user(
    db: AsyncSession, user_id: UUID, data: UserUpdate, current_user: User
) -> User:
    user = await get_user(db, user_id)
    before = {"name": user.name, "email": user.email, "role": user.role, "status": user.status}

    if data.name is not None:
        user.name = data.name
    if data.email is not None:
        # Check uniqueness
        existing = await db.execute(
            select(User).where(User.email == data.email, User.id != user_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="user.email_in_use")
        user.email = data.email
    if data.password is not None:
        from app.utils.security import validate_password_strength
        valid, err_msg = validate_password_strength(data.password)
        if not valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
        user.password_hash = auth_svc.hash_user_password(data.password)
    if data.role is not None:
        user.role = data.role
    if data.status is not None:
        user.status = data.status

    await db.flush()

    after = {"name": user.name, "email": user.email, "role": user.role, "status": user.status}
    await audit_log(
        db,
        user_id=current_user.id,
        action="UPDATE",
        entity_type="user",
        entity_id=user.id,
        before_json=before,
        after_json=after,
    )

    return user


async def delete_user(db: AsyncSession, user_id: UUID, current_user: User) -> None:
    user = await get_user(db, user_id)
    before = {"name": user.name, "email": user.email, "role": user.role, "status": user.status}

    user.status = "inactive"

    await db.flush()

    await audit_log(
        db,
        user_id=current_user.id,
        action="DELETE",
        entity_type="user",
        entity_id=user.id,
        before_json=before,
        after_json={"status": "inactive"},
    )
