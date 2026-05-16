"""Report aggregation service — property stats, lead funnel, recommendation metrics."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.models.property import Property
from app.models.recommendation import Recommendation


async def get_property_stats(db: AsyncSession) -> dict:
    """Aggregate property counts by status."""
    result = await db.execute(
        select(
            Property.status,
            func.count(Property.id).label("count"),
        )
        .where(Property.is_deleted == False)
        .group_by(Property.status)
    )
    rows = result.all()

    status_counts = {row[0]: row[1] for row in rows}
    total = sum(status_counts.values())
    available = status_counts.get("available", 0)
    rented = status_counts.get("rented", 0)
    pending = status_counts.get("pending", 0)
    offline = status_counts.get("offline", 0)
    need_confirm = status_counts.get("need_confirm", 0)

    rental_rate = round(rented / total * 100, 1) if total > 0 else 0
    availability_rate = round(available / total * 100, 1) if total > 0 else 0

    # Price distribution
    price_result = await db.execute(
        select(
            func.min(Property.monthly_rent),
            func.max(Property.monthly_rent),
            func.avg(Property.monthly_rent),
        )
        .where(Property.is_deleted == False, Property.monthly_rent.isnot(None))
    )
    price_row = price_result.one()
    min_price = int(price_row[0]) if price_row[0] else 0
    max_price = int(price_row[1]) if price_row[1] else 0
    avg_price = int(price_row[2]) if price_row[2] else 0

    # Bedroom distribution
    bedroom_result = await db.execute(
        select(
            Property.bedroom_count,
            func.count(Property.id).label("count"),
        )
        .where(Property.is_deleted == False, Property.bedroom_count.isnot(None))
        .group_by(Property.bedroom_count)
        .order_by(Property.bedroom_count)
    )
    bedroom_dist = {str(row[0]): row[1] for row in bedroom_result.all()}

    return {
        "total": total,
        "by_status": {
            "available": available,
            "rented": rented,
            "pending": pending,
            "offline": offline,
            "need_confirm": need_confirm,
        },
        "rental_rate": rental_rate,
        "availability_rate": availability_rate,
        "price": {
            "min": min_price,
            "max": max_price,
            "avg": avg_price,
        },
        "bedroom_distribution": bedroom_dist,
    }


async def get_lead_funnel(db: AsyncSession, days: int = 30) -> dict:
    """Lead conversion funnel over the last N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    base = select(func.count(Lead.id)).where(Lead.created_at >= cutoff)
    total = (await db.execute(base)).scalar() or 0

    stages = ["new", "parsed", "recommended", "contacted", "viewing", "closed"]
    funnel: list[dict] = []
    for stage in stages:
        if stage == "new":
            count = total
        else:
            stage_result = await db.execute(
                base.where(Lead.status == stage)
            )
            count = stage_result.scalar() or 0
        funnel.append({"stage": stage, "count": count})

    # Source breakdown
    source_result = await db.execute(
        select(Lead.source, func.count(Lead.id))
        .where(Lead.created_at >= cutoff)
        .group_by(Lead.source)
    )
    source_breakdown = {row[0] or "unknown": row[1] for row in source_result.all()}

    return {
        "period_days": days,
        "total_leads": total,
        "funnel": funnel,
        "by_source": source_breakdown,
    }


async def get_recommendation_stats(db: AsyncSession, days: int = 30) -> dict:
    """Recommendation metrics over the last N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    total_result = await db.execute(
        select(func.count(Recommendation.id)).where(
            Recommendation.created_at >= cutoff
        )
    )
    total_recs = total_result.scalar() or 0

    sent_result = await db.execute(
        select(func.count(Recommendation.id)).where(
            Recommendation.created_at >= cutoff,
            Recommendation.sent_to_customer == True,
        )
    )
    sent_count = sent_result.scalar() or 0

    # Average match score
    avg_score_result = await db.execute(
        select(func.avg(Recommendation.match_score)).where(
            Recommendation.created_at >= cutoff,
            Recommendation.match_score.isnot(None),
        )
    )
    avg_score = round(avg_score_result.scalar() or 0, 3)

    # Top recommended properties
    top_result = await db.execute(
        select(
            Property.name,
            Property.property_code,
            func.count(Recommendation.id).label("rec_count"),
        )
        .join(Recommendation, Recommendation.property_id == Property.id)
        .where(Recommendation.created_at >= cutoff)
        .group_by(Property.id, Property.name, Property.property_code)
        .order_by(func.count(Recommendation.id).desc())
        .limit(10)
    )
    top_properties = [
        {"name": row[0], "property_code": row[1], "recommendation_count": row[2]}
        for row in top_result.all()
    ]

    # Daily recommendation trend
    daily_result = await db.execute(
        select(
            func.date(Recommendation.created_at).label("date"),
            func.count(Recommendation.id).label("count"),
        )
        .where(Recommendation.created_at >= cutoff)
        .group_by(func.date(Recommendation.created_at))
        .order_by("date")
    )
    daily_trend = [
        {"date": str(row[0]), "count": row[1]} for row in daily_result.all()
    ]

    return {
        "period_days": days,
        "total_recommendations": total_recs,
        "sent_to_customer": sent_count,
        "send_rate": round(sent_count / total_recs * 100, 1) if total_recs > 0 else 0,
        "average_match_score": avg_score,
        "top_properties": top_properties,
        "daily_trend": daily_trend,
    }
