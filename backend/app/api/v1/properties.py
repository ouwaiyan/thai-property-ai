from math import ceil
from uuid import UUID

import csv
import io
from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin_or_manager, require_data_entry, get_current_user
from app.dependencies import get_db
from app.models.user import User
from app.utils.field_permission import apply_field_permissions
from app.schemas import MessageResponse, PaginatedResponse
from app.schemas.property import (
    PropertyCreate,
    PropertyImageOut,
    PropertyListOut,
    PropertyOut,
    PropertyUpdate,
)
from app.services import property_image_service, property_service

router = APIRouter(prefix="/properties", tags=["Properties"])


@router.get("/", response_model=PaginatedResponse)
async def list_properties(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
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
    lat: float | None = Query(None, ge=-90, le=90),
    lng: float | None = Query(None, ge=-180, le=180),
    radius_meters: float | None = Query(None, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = await property_service.get_properties(
        db,
        current_user,
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        min_price=min_price,
        max_price=max_price,
        min_bedrooms=min_bedrooms,
        max_bedrooms=max_bedrooms,
        district=district,
        assigned_agent_id=assigned_agent_id,
        sort_by=sort_by,
        sort_order=sort_order,
        lat=lat,
        lng=lng,
        radius_meters=radius_meters,
    )
    out_items = []
    for p in items:
        validated = PropertyListOut.model_validate(p)
        dist = getattr(p, "_distance_meters", None)
        if dist is not None:
            validated.distance_meters = round(dist, 1)
        # Apply field-level permission masking
        masked = apply_field_permissions(validated.model_dump(), current_user.role)
        out_items.append(PropertyListOut(**masked))
    return PaginatedResponse(
        items=out_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total > 0 else 0,
    )


@router.post("/", response_model=PropertyOut, status_code=201)
async def create_property(
    body: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_data_entry),
):
    prop = await property_service.create_property(db, body, current_user)
    return PropertyOut.model_validate(prop)


@router.get("/{property_id}", response_model=PropertyOut)
async def get_property(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prop = await property_service.get_property(db, property_id, current_user)
    validated = PropertyOut.model_validate(prop)
    masked = apply_field_permissions(validated.model_dump(), current_user.role)
    return PropertyOut(**masked)


@router.put("/{property_id}", response_model=PropertyOut)
async def update_property(
    property_id: UUID,
    body: PropertyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_data_entry),
):
    prop = await property_service.update_property(db, property_id, body, current_user)
    return PropertyOut.model_validate(prop)


@router.delete("/{property_id}", response_model=MessageResponse)
async def delete_property(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager),
):
    await property_service.soft_delete_property(db, property_id, current_user)
    return MessageResponse(message="Property deleted successfully")


@router.post("/{property_id}/images", response_model=list[PropertyImageOut])
async def upload_images(
    property_id: UUID,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_data_entry),
):
    images = await property_image_service.upload_images(
        db, property_id, files, current_user
    )
    return [PropertyImageOut.model_validate(img) for img in images]


@router.get("/export/csv")
async def export_properties_csv(
    status: str | None = None,
    district: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export properties as CSV file (filtered by optional status/district)."""
    items, _ = await property_service.get_properties(
        db, current_user,
        page=1, page_size=10000,  # export all matching
        status=status, district=district,
        sort_by="created_at", sort_order="desc",
    )

    output = io.StringIO()
    output.write('﻿')  # BOM for Excel UTF-8
    writer = csv.writer(output)
    writer.writerow([
        "property_code", "name", "building_name", "address",
        "latitude", "longitude", "district", "area",
        "nearest_bts", "nearest_mrt", "bedroom_count", "bathroom_count",
        "size_sqm", "monthly_rent", "deposit_months", "status",
        "available_date", "pet_allowed", "contact_person",
        "contact_phone", "contact_line", "description", "tags",
        "created_at", "updated_at",
    ])
    for p in items:
        writer.writerow([
            p.property_code, p.name, getattr(p, 'building_name', '') or '',
            p.address or '', p.latitude, p.longitude,
            p.district or '', getattr(p, 'area', '') or '',
            getattr(p, 'nearest_bts', '') or '', getattr(p, 'nearest_mrt', '') or '',
            p.bedroom_count, p.bathroom_count, p.size_sqm,
            p.monthly_rent, p.deposit_months, p.status,
            str(p.available_date) if getattr(p, 'available_date', None) else '',
            'yes' if getattr(p, 'pet_allowed', False) else 'no',
            getattr(p, 'contact_person', '') or '',
            getattr(p, 'contact_phone', '') or '',
            getattr(p, 'contact_line', '') or '',
            getattr(p, 'description', '') or '',
            ','.join(p.tags) if p.tags else '',
            p.created_at.isoformat() if p.created_at else '',
            p.updated_at.isoformat() if p.updated_at else '',
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=properties_export.csv"},
    )


@router.post("/bulk-update", response_model=MessageResponse)
async def bulk_update_properties(
    property_ids: list[UUID],
    status: str | None = None,
    tags: list[str] | None = None,
    assigned_agent_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_or_manager),
):
    """Bulk update status, tags, or assigned agent for multiple properties."""
    await property_service.bulk_update(
        db, property_ids, current_user,
        status=status, tags=tags, assigned_agent_id=assigned_agent_id,
    )
    return MessageResponse(message=f"Updated {len(property_ids)} properties")


@router.delete("/images/{image_id}", response_model=MessageResponse)
async def delete_image(
    image_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_data_entry),
):
    await property_image_service.delete_image(db, image_id, current_user)
    return MessageResponse(message="Image deleted successfully")
