"""Leads CRUD + AI parsing."""
from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_data_entry
from app.dependencies import get_db
from app.utils.field_permission import apply_field_permissions
from app.models.lead import Lead
from app.models.user import User
from app.schemas import PaginatedResponse
from app.schemas.lead import LeadCreate, LeadOut, LeadUpdate
from app.services.ai_service import ai_parse_lead_needs
from app.services.n8n_service import trigger_new_lead_notification, trigger_lead_status_change

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.get("/", response_model=PaginatedResponse)
async def list_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    search: str | None = None,
    source: str | None = None,
    line_user_id: str | None = None,
    assigned_agent_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Lead)
    count_query = select(func.count(Lead.id))

    if current_user.role == "Agent":
        query = query.where(Lead.assigned_agent_id == current_user.id)
        count_query = count_query.where(Lead.assigned_agent_id == current_user.id)

    if status:
        query = query.where(Lead.status == status)
        count_query = count_query.where(Lead.status == status)

    if search:
        search_filter = or_(
            Lead.name.ilike(f"%{search}%"),
            Lead.original_message.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if source:
        query = query.where(Lead.source == source)
        count_query = count_query.where(Lead.source == source)

    if line_user_id:
        query = query.where(Lead.line_user_id == line_user_id)
        count_query = count_query.where(Lead.line_user_id == line_user_id)

    if assigned_agent_id:
        query = query.where(Lead.assigned_agent_id == assigned_agent_id)
        count_query = count_query.where(Lead.assigned_agent_id == assigned_agent_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Lead.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    masked_items = [
        LeadOut(**apply_field_permissions(LeadOut.model_validate(item).model_dump(), current_user.role))
        for item in items
    ]
    return PaginatedResponse(
        items=masked_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total > 0 else 0,
    )


@router.post("/", response_model=LeadOut, status_code=201)
async def create_lead(
    body: LeadCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = Lead(**body.model_dump())
    db.add(lead)
    await db.flush()
    # n8n: notify on new lead
    await trigger_new_lead_notification(db, str(lead.id), lead.name)
    return LeadOut.model_validate(lead)


@router.get("/{lead_id}", response_model=LeadOut)
async def get_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="lead.not_found")
    return LeadOut.model_validate(lead)


@router.put("/{lead_id}", response_model=LeadOut)
async def update_lead(
    lead_id: UUID,
    body: LeadUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_data_entry),
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="lead.not_found")
    old_status = lead.status
    update_data = body.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(lead, key, value)
    await db.flush()
    # n8n: notify on status change
    if "status" in update_data and update_data["status"] != old_status:
        await trigger_lead_status_change(str(lead.id), old_status, lead.status, lead.name)
    return LeadOut.model_validate(lead)


@router.post("/{lead_id}/parse", response_model=LeadOut)
async def parse_lead_needs(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_data_entry),
):
    """AI-parse a lead's original message and update parsed_needs."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="lead.not_found")

    parsed = await ai_parse_lead_needs(db, lead.original_message, lead.language)

    lead.parsed_needs = parsed.model_dump()
    lead.target_location = parsed.target_location
    lead.budget_min = parsed.budget_min
    lead.budget_max = parsed.budget_max
    lead.bedroom_count = parsed.bedroom_count
    lead.pet_required = parsed.pet_required
    lead.preferred_transport = parsed.preferred_transport
    lead.tags = parsed.tags
    if lead.status == "new":
        lead.status = "parsed"

    await db.flush()
    return LeadOut.model_validate(lead)
