"""Property recommendation engine with match scoring.

Formula: distance*0.40 + budget*0.25 + bedroom*0.20 + tag*0.10 + freshness*0.05
"""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_DWithin, ST_Distance
from geoalchemy2.elements import WKTElement

from app.models.lead import Lead
from app.models.property import Property
from app.utils.geo import geocode, haversine_distance


def _compute_match_score(
    prop: Property,
    lead: Lead,
    distance_meters: float | None,
) -> dict:
    """Compute match score and breakdown for a property-lead pair."""
    reasons: list[str] = []

    # 1. Distance score (40%)
    if distance_meters is not None:
        if distance_meters <= 500:
            distance_score = 1.0
            reasons.append("距离目标地点500米内")
        elif distance_meters <= 1000:
            distance_score = 0.8
        elif distance_meters <= 3000:
            distance_score = 0.5
        elif distance_meters <= 5000:
            distance_score = 0.3
        else:
            distance_score = 0.1
    else:
        distance_score = 0.3

    # 2. Budget score (25%)
    if lead.budget_min is not None and lead.budget_max is not None and prop.monthly_rent is not None:
        if lead.budget_min <= prop.monthly_rent <= lead.budget_max:
            budget_score = 1.0
            reasons.append("在客户预算范围内")
        elif prop.monthly_rent < lead.budget_min * 0.8:
            budget_score = 0.6
            reasons.append("低于客户预算")
        elif prop.monthly_rent > lead.budget_max * 1.2:
            budget_score = 0.2
            reasons.append("超出客户预算")
        else:
            budget_score = 0.7
    else:
        budget_score = 0.5

    # 3. Bedroom match (20%)
    bedroom_score = 0.5
    if lead.bedroom_count is not None and prop.bedroom_count is not None:
        if lead.bedroom_count == prop.bedroom_count:
            bedroom_score = 1.0
            reasons.append(f"户型匹配({lead.bedroom_count}卧)")
        elif abs(lead.bedroom_count - prop.bedroom_count) == 1:
            bedroom_score = 0.6
        else:
            bedroom_score = 0.2

    # 4. Pet bonus/penalty (within bedroom factor)
    if lead.pet_required and prop.pet_allowed:
        reasons.append("允许养宠物")
        bedroom_score = min(bedroom_score + 0.1, 1.0)
    elif lead.pet_required and not prop.pet_allowed:
        bedroom_score *= 0.5

    # 5. Tag overlap (10%)
    lead_tags = set((t or "").lower() for t in (lead.tags or []))
    prop_tags = set((t or "").lower() for t in (prop.tags or []))
    if lead_tags and prop_tags:
        overlap = len(lead_tags & prop_tags)
        tag_score = min(overlap / max(len(lead_tags), 1), 1.0)
        if overlap > 0:
            reasons.append(f"标签匹配: {', '.join(lead_tags & prop_tags)}")
    else:
        tag_score = 0.5

    # 6. Freshness (5%)
    if prop.created_at:
        days_old = (datetime.now(timezone.utc) - prop.created_at).days
        if days_old <= 7:
            freshness_score = 1.0
        elif days_old <= 30:
            freshness_score = 0.7
        elif days_old <= 90:
            freshness_score = 0.5
        else:
            freshness_score = 0.3
    else:
        freshness_score = 0.5

    total = (
        distance_score * 0.40
        + budget_score * 0.25
        + bedroom_score * 0.20
        + tag_score * 0.10
        + freshness_score * 0.05
    )

    return {
        "total": round(total, 4),
        "breakdown": {
            "distance": round(distance_score * 0.40, 4),
            "budget": round(budget_score * 0.25, 4),
            "bedroom": round(bedroom_score * 0.20, 4),
            "tag": round(tag_score * 0.10, 4),
            "freshness": round(freshness_score * 0.05, 4),
        },
        "reasons": reasons,
    }


async def search_recommendations(
    db: AsyncSession,
    lead: Lead,
    limit: int = 20,
    max_distance_meters: int | None = None,
    route_mode: str = "DRIVE",
) -> tuple[list[dict], int]:
    """Search properties and score them against a lead's needs.

    Steps:
    1. Base query — available, not deleted
    2. Pre-filter by bedroom, budget, pet
    3. Geocode lead's target_location for distance
    4. Score each candidate
    5. Sort by score desc, return top N
    """

    query = select(Property).where(
        Property.status == "available",
        Property.is_deleted == False,
    )

    if lead.bedroom_count is not None:
        query = query.where(
            Property.bedroom_count >= lead.bedroom_count - 1,
            Property.bedroom_count <= lead.bedroom_count + 1,
        )

    if lead.budget_min is not None and lead.budget_max is not None:
        query = query.where(
            Property.monthly_rent >= int(lead.budget_min * 0.8),
            Property.monthly_rent <= int(lead.budget_max * 1.2),
        )
    elif lead.budget_max is not None:
        query = query.where(Property.monthly_rent <= int(lead.budget_max * 1.2))

    if lead.pet_required:
        query = query.where(Property.pet_allowed == True)

    # Geocode lead location
    origin_lat: float | None = None
    origin_lng: float | None = None
    if lead.target_location:
        try:
            geo_results = await geocode(lead.target_location, db=db)
            if geo_results:
                origin_lat = geo_results[0].latitude
                origin_lng = geo_results[0].longitude
        except Exception:
            pass

    # ── PostGIS spatial pre-filter ──────────────────────────────────
    distance_expr = None
    if origin_lat is not None and origin_lng is not None:
        ref_point = WKTElement(f"POINT({origin_lng} {origin_lat})", srid=4326)
        query = query.where(Property.location_geo.isnot(None))
        if max_distance_meters is not None:
            query = query.where(
                ST_DWithin(Property.location_geo, ref_point, max_distance_meters)
            )
        distance_expr = ST_Distance(Property.location_geo, ref_point).label("distance_meters")
        query = query.add_columns(distance_expr)

    result = await db.execute(query)

    # Score each candidate
    scored: list[tuple[Property, float | None, dict]] = []
    if distance_expr is not None:
        rows = result.all()
        for row in rows:
            prop = row[0]
            distance = float(row[1]) if row[1] is not None else None
            score_result = _compute_match_score(prop, lead, distance)
            scored.append((prop, distance, score_result))
    else:
        candidates = list(result.scalars().all())
        for prop in candidates:
            distance: float | None = None
            if (
                origin_lat is not None
                and origin_lng is not None
                and prop.latitude is not None
                and prop.longitude is not None
            ):
                distance = haversine_distance(
                    origin_lat, origin_lng, prop.latitude, prop.longitude
                )
                if max_distance_meters is not None and distance > max_distance_meters:
                    continue
            score_result = _compute_match_score(prop, lead, distance)
            scored.append((prop, distance, score_result))

    scored.sort(key=lambda x: x[2]["total"], reverse=True)

    total_scanned = len(scored)
    top = scored[:limit]

    results: list[dict] = []
    for prop, distance, score_result in top:
        results.append({
            "property_id": prop.id,
            "property_code": prop.property_code,
            "name": prop.name,
            "monthly_rent": prop.monthly_rent or 0,
            "bedroom_count": prop.bedroom_count or 0,
            "district": prop.district or "",
            "latitude": prop.latitude,
            "longitude": prop.longitude,
            "distance_meters": round(distance, 1) if distance else None,
            "duration_minutes": None,
            "match_score": score_result["total"],
            "score_breakdown": score_result["breakdown"],
            "reasons": score_result["reasons"],
        })

    return results, total_scanned
