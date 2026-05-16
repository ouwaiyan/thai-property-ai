from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LeadCreate(BaseModel):
    name: str = Field(..., max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    language: str = Field(default="zh", pattern=r"^(zh|en|th)$")
    original_message: str
    source: str = Field(default="web", pattern=r"^(web|line|csv)$")
    line_user_id: Optional[str] = Field(None, max_length=64)
    assigned_agent_id: Optional[UUID] = None


class LeadUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = None
    status: Optional[str] = None
    assigned_agent_id: Optional[UUID] = None


class LeadOut(BaseModel):
    id: UUID
    name: str
    phone: Optional[str]
    language: str
    original_message: str
    parsed_needs: Optional[dict]
    target_location: Optional[str]
    budget_min: Optional[int]
    budget_max: Optional[int]
    bedroom_count: Optional[int]
    pet_required: bool
    preferred_transport: Optional[str]
    tags: Optional[list[str]]
    status: str
    source: str
    line_user_id: Optional[str]
    assigned_agent_id: Optional[UUID]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}
