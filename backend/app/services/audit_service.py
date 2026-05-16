from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log(
    db: AsyncSession,
    user_id: UUID,
    action: str,
    entity_type: str,
    entity_id: UUID | None = None,
    before_json: dict | None = None,
    after_json: dict | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_json=before_json,
        after_json=after_json,
        ip_address=ip_address,
    )
    db.add(entry)
    await db.flush()
    return entry


async def get_logs(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    user_id: UUID | None = None,
    action: str | None = None,
    entity_type: str | None = None,
) -> tuple[list[AuditLog], int]:
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))

    if user_id:
        query = query.where(AuditLog.user_id == user_id)
        count_query = count_query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
        count_query = count_query.where(AuditLog.entity_type == entity_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    items = list(result.scalars().all())

    return items, total
