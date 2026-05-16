from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.dependencies import get_db
from app.models.user import User
from app.schemas import PaginatedResponse
from app.schemas.audit_log import AuditLogOut
from app.services import audit_service

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("/", response_model=PaginatedResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: UUID | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    items, total = await audit_service.get_logs(
        db,
        page=page,
        page_size=page_size,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
    )
    return PaginatedResponse(
        items=[AuditLogOut.model_validate(log) for log in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total > 0 else 0,
    )
