import uuid as _uuid
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from geoalchemy2.functions import ST_DWithin, ST_Distance
from geoalchemy2.elements import WKTElement

from app.models.property import Property
from app.models.property_image import PropertyImage
from app.models.user import User
from app.schemas.property import PropertyCreate, PropertyUpdate
from app.services.audit_service import log as audit_log


def _row_to_before(prop: Property) -> dict:
    return {
        "name": prop.name,
        "property_code": prop.property_code,
        "status": prop.status,
        "monthly_rent": prop.monthly_rent,
        "bedroom_count": prop.bedroom_count,
        "district": prop.district,
        "address": prop.address,
        "latitude": prop.latitude,
        "longitude": prop.longitude,
        "pet_allowed": prop.pet_allowed,
        "tags": prop.tags,
    }


async def get_properties(
    db: AsyncSession,
    current_user: User,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    status: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    min_bedrooms: int | None = None,
    max_bedrooms: int | None = None,
    district: str | None = None,
    assigned_agent_id: UUID | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    lat: float | None = None,
    lng: float | None = None,
    radius_meters: float | None = None,
) -> tuple[list[Property], int]:
    query = select(Property)
    count_query = select(func.count(Property.id))

    # Agent sees only their own properties
    if current_user.role == "Agent":
        query = query.where(Property.created_by == current_user.id)
        count_query = count_query.where(Property.created_by == current_user.id)

    query = query.options(selectinload(Property.images))

    if search:
        filter_expr = or_(
            Property.name.ilike(f"%{search}%"),
            Property.address.ilike(f"%{search}%"),
            Property.building_name.ilike(f"%{search}%"),
            Property.contact_person.ilike(f"%{search}%"),
            Property.contact_phone.ilike(f"%{search}%"),
            Property.contact_line.ilike(f"%{search}%"),
        )
        query = query.where(filter_expr)
        count_query = count_query.where(filter_expr)

    if status:
        query = query.where(Property.status == status)
        count_query = count_query.where(Property.status == status)
    if min_price is not None:
        query = query.where(Property.monthly_rent >= min_price)
        count_query = count_query.where(Property.monthly_rent >= min_price)
    if max_price is not None:
        query = query.where(Property.monthly_rent <= max_price)
        count_query = count_query.where(Property.monthly_rent <= max_price)
    if min_bedrooms is not None:
        query = query.where(Property.bedroom_count >= min_bedrooms)
        count_query = count_query.where(Property.bedroom_count >= min_bedrooms)
    if max_bedrooms is not None:
        query = query.where(Property.bedroom_count <= max_bedrooms)
        count_query = count_query.where(Property.bedroom_count <= max_bedrooms)
    if district:
        query = query.where(Property.district.ilike(f"%{district}%"))
        count_query = count_query.where(Property.district.ilike(f"%{district}%"))
    if assigned_agent_id:
        query = query.where(Property.assigned_agent_id == assigned_agent_id)
        count_query = count_query.where(Property.assigned_agent_id == assigned_agent_id)

    # ── Geo filtering (PostGIS spatial index) ────────────────────────
    distance_expr = None
    if lat is not None and lng is not None:
        ref_point = WKTElement(f"POINT({lng} {lat})", srid=4326)
        distance_expr = ST_Distance(Property.location_geo, ref_point).label("distance_meters")

        query = query.where(Property.location_geo.isnot(None))
        count_query = count_query.where(Property.location_geo.isnot(None))

        if radius_meters is not None:
            query = query.where(ST_DWithin(Property.location_geo, ref_point, radius_meters))
            count_query = count_query.where(ST_DWithin(Property.location_geo, ref_point, radius_meters))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    if distance_expr is not None:
        if sort_by == "distance":
            query = query.order_by(distance_expr.asc())
        else:
            sort_col = getattr(Property, sort_by, Property.created_at)
            if sort_order == "asc":
                query = query.order_by(sort_col.asc())
            else:
                query = query.order_by(sort_col.desc())
        query = query.add_columns(distance_expr)
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        rows = result.all()
        items = []
        for row in rows:
            prop = row[0]
            prop._distance_meters = float(row[1]) if row[1] is not None else None
            items.append(prop)
    else:
        sort_col = getattr(Property, sort_by, Property.created_at)
        if sort_order == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        items = list(result.scalars().all())

    return items, total


async def get_property(db: AsyncSession, property_id: UUID, current_user: User) -> Property:
    result = await db.execute(
        select(Property).options(selectinload(Property.images)).where(Property.id == property_id)
    )
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="property.not_found")

    if current_user.role == "Agent" and str(prop.created_by) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="property.access_denied")

    return prop


async def create_property(
    db: AsyncSession, data: PropertyCreate, current_user: User
) -> Property:
    # Check property_code uniqueness
    existing = await db.execute(
        select(Property).where(Property.property_code == data.property_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="property.code_exists",
        )

    prop = Property(
        created_by=current_user.id,
        **data.model_dump(exclude={"assigned_agent_id"}, exclude_none=True),
        assigned_agent_id=data.assigned_agent_id if "assigned_agent_id" in data.model_dump(exclude_none=True) else None,
    )
    db.add(prop)
    await db.flush()

    await audit_log(
        db, user_id=current_user.id, action="CREATE", entity_type="property",
        entity_id=prop.id, after_json=_row_to_before(prop),
    )
    return prop


async def update_property(
    db: AsyncSession, property_id: UUID, data: PropertyUpdate, current_user: User
) -> Property:
    prop = await get_property(db, property_id, current_user)

    # Agent can only update own properties
    if current_user.role == "Agent" and str(prop.created_by) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="property.access_denied")

    before = _row_to_before(prop)
    update_data = data.model_dump(exclude_none=True)

    if "property_code" in update_data and update_data["property_code"] != prop.property_code:
        existing = await db.execute(
            select(Property).where(Property.property_code == update_data["property_code"])
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="property.code_in_use")

    for key, value in update_data.items():
        setattr(prop, key, value)

    await db.flush()

    await audit_log(
        db, user_id=current_user.id, action="UPDATE", entity_type="property",
        entity_id=prop.id, before_json=before, after_json=_row_to_before(prop),
    )
    return prop


async def bulk_update(
    db: AsyncSession,
    property_ids: list[UUID],
    current_user: User,
    status: str | None = None,
    tags: list[str] | None = None,
    assigned_agent_id: UUID | None = None,
) -> None:
    """Bulk update status, tags, or assigned agent on multiple properties."""
    from app.services.audit_service import log as audit_log

    result = await db.execute(
        select(Property).where(Property.id.in_(property_ids))
    )
    props = list(result.scalars().all())
    for prop in props:
        before = _row_to_before(prop)
        if status is not None:
            prop.status = status
        if tags is not None:
            prop.tags = tags
        if assigned_agent_id is not None:
            prop.assigned_agent_id = assigned_agent_id
        await db.flush()
        await audit_log(
            db, user_id=current_user.id, action="BULK_UPDATE", entity_type="property",
            entity_id=prop.id, before_json=before,
            after_json={"status": prop.status, "tags": prop.tags, "assigned_agent_id": str(prop.assigned_agent_id) if prop.assigned_agent_id else None},
        )


async def soft_delete_property(
    db: AsyncSession, property_id: UUID, current_user: User
) -> None:
    prop = await get_property(db, property_id, current_user)
    before = _row_to_before(prop)

    prop.is_deleted = True
    prop.deleted_at = datetime.utcnow()

    await db.flush()

    await audit_log(
        db, user_id=current_user.id, action="DELETE", entity_type="property",
        entity_id=prop.id, before_json=before, after_json={"is_deleted": True},
    )
