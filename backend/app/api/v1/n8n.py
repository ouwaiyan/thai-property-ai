"""n8n automation endpoints — data endpoints for scheduled workflows and webhook triggers."""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_user, require_admin
from app.dependencies import get_db
from app.models.user import User
from app.schemas.n8n import (
    DailyStatsResponse,
    N8NTriggerRequest,
    N8NTriggerResponse,
    StalePropertyItem,
    UnfollowedLeadItem,
)
from app.services.n8n_service import (
    get_daily_stats,
    get_stale_properties,
    get_unfollowed_leads,
)

router = APIRouter(prefix="/n8n", tags=["n8n"])


@router.get("/daily-stats", response_model=DailyStatsResponse)
async def daily_stats(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Daily statistics for the 9:00 report workflow."""
    return await get_daily_stats(db)


@router.get("/stale-properties", response_model=list[StalePropertyItem])
async def stale_properties(
    days: int = Query(7, ge=1, le=90, description="Days since last update"),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Properties not updated in N days — for stale-property reminder workflow."""
    return await get_stale_properties(db, days_since_update=days)


@router.get("/unfollowed-leads", response_model=list[UnfollowedLeadItem])
async def unfollowed_leads(
    hours: int = Query(24, ge=1, le=168, description="Hours without follow-up"),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Leads not followed up in N hours — for follow-up reminder workflow."""
    return await get_unfollowed_leads(db, hours_unfollowed=hours)
