"""n8n-related Pydantic schemas."""
from datetime import datetime

from pydantic import BaseModel, Field


class DailyStatsResponse(BaseModel):
    date: str
    new_leads_today: int
    recommendations_today: int
    properties: dict
    leads_pending_reply: int


class StalePropertyItem(BaseModel):
    id: str
    property_code: str
    name: str
    status: str
    monthly_rent: int | None = None
    district: str | None = None
    updated_at: str | None = None


class UnfollowedLeadItem(BaseModel):
    id: str
    name: str
    status: str
    phone: str | None = None
    line_user_id: str | None = None
    source: str | None = None
    target_location: str | None = None
    updated_at: str | None = None


class N8NTriggerRequest(BaseModel):
    event: str = Field(..., description="Event type: new_lead, import_complete, lead_status_change")
    payload: dict = Field(default_factory=dict)


class N8NTriggerResponse(BaseModel):
    success: bool
    message: str = ""
