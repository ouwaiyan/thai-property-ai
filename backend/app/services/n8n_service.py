"""n8n automation service — webhook triggers and scheduled-task data endpoints.

The backend fires webhooks to n8n for real-time events. n8n polls the
backend for scheduled reports (daily stats, stale properties, unfollowed leads).
"""
import json
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.lead import Lead
from app.models.property import Property


async def _call_n8n_webhook(event_type: str, payload: dict) -> bool:
    """Call the configured n8n webhook URL with an event payload."""
    url = getattr(settings, "N8N_WEBHOOK_URL", "")
    if not url:
        return False
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                url,
                json={"event": event_type, "payload": payload},
                headers={"Content-Type": "application/json"},
            )
            return resp.status_code in (200, 202, 204)
    except Exception:
        return False


async def trigger_new_lead_notification(db: AsyncSession, lead_id: str, lead_name: str) -> None:
    """Notify agents/managers when a new lead is created."""
    payload = {"lead_id": lead_id, "lead_name": lead_name, "action": "new_lead"}
    await _call_n8n_webhook("new_lead", payload)


async def trigger_import_complete(
    db: AsyncSession,
    job_id: str,
    filename: str,
    total_rows: int,
    success_rows: int,
    error_rows: int,
) -> None:
    """Notify when a batch import finishes."""
    payload = {
        "import_job_id": job_id,
        "filename": filename,
        "total_rows": total_rows,
        "success_rows": success_rows,
        "error_rows": error_rows,
        "action": "import_complete",
    }
    await _call_n8n_webhook("import_complete", payload)


async def trigger_lead_status_change(
    lead_id: str, old_status: str, new_status: str, lead_name: str
) -> None:
    """Notify when a lead's status changes."""
    payload = {
        "lead_id": lead_id,
        "lead_name": lead_name,
        "old_status": old_status,
        "new_status": new_status,
    }
    await _call_n8n_webhook("lead_status_change", payload)


async def get_daily_stats(db: AsyncSession) -> dict:
    """Return daily statistics for the n8n daily report workflow (TABLE 12 row 4)."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # New leads today
    leads_result = await db.execute(
        select(func.count(Lead.id)).where(Lead.created_at >= today_start)
    )
    new_leads_today = leads_result.scalar() or 0

    # Recommendations today
    from app.models.recommendation import Recommendation

    recs_result = await db.execute(
        select(func.count(Recommendation.id)).where(
            Recommendation.created_at >= today_start
        )
    )
    recommendations_today = recs_result.scalar() or 0

    # Property counts by status
    avail_result = await db.execute(
        select(func.count(Property.id)).where(
            Property.status == "available", Property.is_deleted == False
        )
    )
    available = avail_result.scalar() or 0
    pending_result = await db.execute(
        select(func.count(Property.id)).where(
            Property.status == "pending", Property.is_deleted == False
        )
    )
    pending = pending_result.scalar() or 0
    rented_result = await db.execute(
        select(func.count(Property.id)).where(
            Property.status == "rented", Property.is_deleted == False
        )
    )
    rented = rented_result.scalar() or 0
    total_result = await db.execute(
        select(func.count(Property.id)).where(Property.is_deleted == False)
    )
    total = total_result.scalar() or 0

    # Leads pending reply
    pending_reply_result = await db.execute(
        select(func.count(Lead.id)).where(Lead.status == "pending_reply")
    )
    pending_reply = pending_reply_result.scalar() or 0

    return {
        "date": today_start.strftime("%Y-%m-%d"),
        "new_leads_today": new_leads_today,
        "recommendations_today": recommendations_today,
        "properties": {
            "total": total,
            "available": available,
            "pending": pending,
            "rented": rented,
        },
        "leads_pending_reply": pending_reply,
    }


async def get_stale_properties(
    db: AsyncSession, days_since_update: int = 7
) -> list[dict]:
    """Return properties not updated in N days (TABLE 12 row 3)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_since_update)

    result = await db.execute(
        select(Property).where(
            Property.is_deleted == False,
            Property.status.in_(["available", "pending"]),
            Property.updated_at < cutoff,
        ).order_by(Property.updated_at.asc()).limit(50)
    )
    props = list(result.scalars().all())

    return [
        {
            "id": str(p.id),
            "property_code": p.property_code,
            "name": p.name,
            "status": p.status,
            "monthly_rent": p.monthly_rent,
            "district": p.district,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in props
    ]


async def get_unfollowed_leads(
    db: AsyncSession, hours_unfollowed: int = 24
) -> list[dict]:
    """Return leads not followed up in N hours (TABLE 12 row 2)."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_unfollowed)

    result = await db.execute(
        select(Lead).where(
            Lead.status.in_(["new", "parsed", "pending_reply"]),
            Lead.updated_at < cutoff,
        ).order_by(Lead.updated_at.asc()).limit(50)
    )
    leads = list(result.scalars().all())

    return [
        {
            "id": str(l.id),
            "name": l.name,
            "status": l.status,
            "phone": l.phone,
            "line_user_id": l.line_user_id,
            "source": l.source,
            "target_location": l.target_location,
            "updated_at": l.updated_at.isoformat() if l.updated_at else None,
        }
        for l in leads
    ]
