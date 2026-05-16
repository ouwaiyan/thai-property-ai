"""Reports API — property stats, lead funnel, recommendation metrics."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin_or_manager
from app.dependencies import get_db
from app.models.user import User
from app.services.report_service import (
    get_lead_funnel,
    get_property_stats,
    get_recommendation_stats,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/properties")
async def property_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Property statistics: status breakdown, price distribution, bedroom distribution."""
    return await get_property_stats(db)


@router.get("/leads")
async def lead_report(
    days: int = Query(30, ge=1, le=365, description="Period in days"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lead conversion funnel and source breakdown."""
    return await get_lead_funnel(db, days=days)


@router.get("/recommendations")
async def recommendation_report(
    days: int = Query(30, ge=1, le=365, description="Period in days"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recommendation metrics: counts, send rate, avg score, top properties, daily trend."""
    return await get_recommendation_stats(db, days=days)
