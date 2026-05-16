"""Recommendation search and management."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.dependencies import get_db
from app.models.lead import Lead
from app.models.recommendation import Recommendation
from app.models.user import User
from app.schemas.ai import (
    MarkSentResponse,
    RecommendationOut,
    RecommendationSearchRequest,
    RecommendationSearchResponse,
    RecommendationSearchResult,
    SaveMessageRequest,
)
from app.models.property import Property
from app.services.recommendation_service import search_recommendations

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post("/search", response_model=RecommendationSearchResponse)
async def search(
    body: RecommendationSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search properties and score them against lead needs."""
    lead_result = await db.execute(select(Lead).where(Lead.id == body.lead_id))
    lead = lead_result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="lead.not_found")

    results, total_scanned = await search_recommendations(
        db, lead, limit=body.limit,
        max_distance_meters=body.max_distance_meters,
        route_mode=body.route_mode,
    )

    for r in results:
        rec = Recommendation(
            lead_id=lead.id,
            property_id=r["property_id"],
            distance_meters=int(r["distance_meters"]) if r.get("distance_meters") else None,
            duration_minutes=r.get("duration_minutes"),
            route_mode=body.route_mode,
            match_score=r["match_score"],
            reason_json={
                "breakdown": r["score_breakdown"],
                "reasons": r["reasons"],
            },
        )
        db.add(rec)
    await db.flush()

    return RecommendationSearchResponse(
        lead_id=body.lead_id,
        results=[RecommendationSearchResult(**r) for r in results],
        total_scanned=total_scanned,
    )


@router.get("/by-lead/{lead_id}", response_model=list[RecommendationOut])
async def list_for_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all past recommendations for a lead."""
    result = await db.execute(
        select(Recommendation).where(Recommendation.lead_id == lead_id).order_by(Recommendation.created_at.desc())
    )
    recs = list(result.scalars().all())

    out: list[RecommendationOut] = []
    for rec in recs:
        prop = rec.property
        out.append(RecommendationOut(
            id=rec.id,
            lead_id=rec.lead_id,
            property_id=rec.property_id,
            property_code=prop.property_code if prop else None,
            property_name=prop.name if prop else None,
            monthly_rent=prop.monthly_rent if prop else None,
            bedroom_count=prop.bedroom_count if prop else None,
            district=prop.district if prop else None,
            distance_meters=rec.distance_meters,
            duration_minutes=rec.duration_minutes,
            route_mode=rec.route_mode,
            match_score=rec.match_score,
            reason_json=rec.reason_json,
            ai_message=rec.ai_message,
            sent_to_customer=rec.sent_to_customer,
            created_at=rec.created_at,
        ))
    return out


@router.post("/{recommendation_id}/save-message", response_model=RecommendationOut)
async def save_message(
    recommendation_id: UUID,
    body: SaveMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save an AI-generated message to a recommendation."""
    result = await db.execute(
        select(Recommendation).where(Recommendation.id == recommendation_id)
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="recommendation.not_found")
    rec.ai_message = body.ai_message
    await db.flush()

    prop = rec.property
    return RecommendationOut(
        id=rec.id,
        lead_id=rec.lead_id,
        property_id=rec.property_id,
        property_code=prop.property_code if prop else None,
        property_name=prop.name if prop else None,
        monthly_rent=prop.monthly_rent if prop else None,
        bedroom_count=prop.bedroom_count if prop else None,
        district=prop.district if prop else None,
        distance_meters=rec.distance_meters,
        duration_minutes=rec.duration_minutes,
        route_mode=rec.route_mode,
        match_score=rec.match_score,
        reason_json=rec.reason_json,
        ai_message=rec.ai_message,
        sent_to_customer=rec.sent_to_customer,
        created_at=rec.created_at,
    )


@router.post("/{recommendation_id}/mark-sent", response_model=MarkSentResponse)
async def mark_sent(
    recommendation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Recommendation).where(Recommendation.id == recommendation_id)
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="recommendation.not_found")
    rec.sent_to_customer = True
    await db.flush()
    return MarkSentResponse(
        recommendation_id=rec.id,
        sent_to_customer=True,
    )
