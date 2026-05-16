from typing import Optional
from datetime import datetime, date
from uuid import UUID

from pydantic import BaseModel, Field


class PropertyCreate(BaseModel):
    property_code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=500)
    building_name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    district: Optional[str] = None
    area: Optional[str] = None
    nearest_bts: Optional[str] = None
    nearest_mrt: Optional[str] = None
    bedroom_count: Optional[int] = None
    bathroom_count: Optional[int] = None
    size_sqm: Optional[float] = None
    monthly_rent: Optional[int] = None
    deposit_months: Optional[int] = None
    status: str = "available"
    available_date: Optional[date] = None
    pet_allowed: bool = False
    contact_person: Optional[str] = None
    contact_line: Optional[str] = None
    contact_phone: Optional[str] = None
    description: Optional[str] = None
    internal_note: Optional[str] = None
    tags: Optional[list[str]] = None
    assigned_agent_id: Optional[UUID] = None


class PropertyUpdate(BaseModel):
    property_code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=500)
    building_name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    district: Optional[str] = None
    area: Optional[str] = None
    nearest_bts: Optional[str] = None
    nearest_mrt: Optional[str] = None
    bedroom_count: Optional[int] = None
    bathroom_count: Optional[int] = None
    size_sqm: Optional[float] = None
    monthly_rent: Optional[int] = None
    deposit_months: Optional[int] = None
    status: Optional[str] = None
    available_date: Optional[date] = None
    pet_allowed: Optional[bool] = None
    contact_person: Optional[str] = None
    contact_line: Optional[str] = None
    contact_phone: Optional[str] = None
    description: Optional[str] = None
    internal_note: Optional[str] = None
    tags: Optional[list[str]] = None
    assigned_agent_id: Optional[UUID] = None


class PropertyImageOut(BaseModel):
    id: UUID
    property_id: UUID
    image_url: str
    sort_order: int
    is_cover: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PropertyOut(BaseModel):
    id: UUID
    property_code: str
    name: str
    building_name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    district: Optional[str] = None
    area: Optional[str] = None
    nearest_bts: Optional[str] = None
    nearest_mrt: Optional[str] = None
    bedroom_count: Optional[int] = None
    bathroom_count: Optional[int] = None
    size_sqm: Optional[float] = None
    monthly_rent: Optional[int] = None
    deposit_months: Optional[int] = None
    status: str
    available_date: Optional[date] = None
    pet_allowed: bool = False
    contact_person: Optional[str] = None
    contact_line: Optional[str] = None
    contact_phone: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    created_by: UUID
    assigned_agent_id: Optional[UUID] = None
    images: list[PropertyImageOut] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PropertyListOut(BaseModel):
    id: UUID
    property_code: str
    name: str
    building_name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    district: Optional[str] = None
    area: Optional[str] = None
    nearest_bts: Optional[str] = None
    nearest_mrt: Optional[str] = None
    bedroom_count: Optional[int] = None
    bathroom_count: Optional[int] = None
    size_sqm: Optional[float] = None
    monthly_rent: Optional[int] = None
    status: str
    pet_allowed: bool = False
    contact_person: Optional[str] = None
    contact_line: Optional[str] = None
    contact_phone: Optional[str] = None
    tags: Optional[list[str]] = None
    distance_meters: Optional[float] = None
    created_by: UUID
    assigned_agent_id: Optional[UUID] = None
    images: list[PropertyImageOut] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
