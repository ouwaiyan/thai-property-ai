from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Parse Lead ──

class ParseLeadRequest(BaseModel):
    message: str
    language: str = Field(default="zh", pattern=r"^(zh|en|th)$")
    lead_id: Optional[UUID] = None


class ParseLeadResponse(BaseModel):
    target_location: Optional[str]
    budget_min: Optional[int]
    budget_max: Optional[int]
    bedroom_count: Optional[int]
    pet_required: bool
    preferred_transport: Optional[str]
    tags: list[str]
    missing_fields: list[str]
    follow_up_questions: list[str]


# ── Generate Tags ──

class GenerateTagsRequest(BaseModel):
    property_id: UUID
    language: str = Field(default="zh", pattern=r"^(zh|en|th)$")


class GenerateTagsResponse(BaseModel):
    tags: list[str]
    highlights: list[str]


# ── Generate Sales Copy ──

class GenerateMessageRequest(BaseModel):
    lead_id: UUID
    property_ids: list[UUID] = Field(..., min_length=1, max_length=5)
    language: str = Field(default="zh", pattern=r"^(zh|en|th)$")
    tone: str = Field(default="friendly", pattern=r"^(friendly|professional|urgent)$")


class GenerateMessageResponse(BaseModel):
    messages: list[dict]


# ── Recommendation Search ──

class RecommendationSearchRequest(BaseModel):
    lead_id: UUID
    limit: int = Field(default=20, ge=1, le=50)
    max_distance_meters: Optional[int] = None
    route_mode: str = Field(default="DRIVE", pattern=r"^(DRIVE|WALK|TRANSIT)$")


class RecommendationSearchResult(BaseModel):
    property_id: UUID
    property_code: str
    name: str
    monthly_rent: int
    bedroom_count: int
    district: str
    distance_meters: Optional[float]
    duration_minutes: Optional[int]
    match_score: float
    score_breakdown: dict
    reasons: list[str]


class RecommendationSearchResponse(BaseModel):
    lead_id: UUID
    results: list[RecommendationSearchResult]
    total_scanned: int


# ── Recommendation History ──

class RecommendationOut(BaseModel):
    id: UUID
    lead_id: UUID
    property_id: UUID
    property_code: Optional[str] = None
    property_name: Optional[str] = None
    monthly_rent: Optional[int] = None
    bedroom_count: Optional[int] = None
    district: Optional[str] = None
    distance_meters: Optional[int] = None
    duration_minutes: Optional[int] = None
    route_mode: Optional[str] = None
    match_score: float
    reason_json: Optional[dict] = None
    ai_message: Optional[str] = None
    sent_to_customer: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SaveMessageRequest(BaseModel):
    ai_message: str


# ── Mark Sent ──

class MarkSentResponse(BaseModel):
    recommendation_id: UUID
    sent_to_customer: bool


# ── Data Cleaning ──

class CleanDataRequest(BaseModel):
    column_name: str
    sample_values: list[str]
    expected_type: str = Field(default="auto", pattern=r"^(auto|price|phone|address|district|name)$")


class CleanDataResponse(BaseModel):
    suggestions: list[dict]
    pattern_rule: Optional[str] = None
