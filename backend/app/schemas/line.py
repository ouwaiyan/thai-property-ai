from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── LineMessage ──

class LineMessageOut(BaseModel):
    id: UUID
    line_user_id: str
    lead_id: Optional[UUID] = None
    message_text: str
    direction: str
    message_type: str
    source_type: str
    reply_status: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Conversation ──

class LineConversationOut(BaseModel):
    line_user_id: str
    lead_id: Optional[UUID] = None
    lead_name: Optional[str] = None
    messages: list[LineMessageOut]
    latest_message_at: Optional[datetime] = None


# ── Reply ──

class LineReplyRequest(BaseModel):
    reply_token: str
    message_text: str = Field(..., max_length=5000)
    line_user_id: str | None = None


class LinePushRequest(BaseModel):
    line_user_id: str
    message_text: str = Field(..., max_length=5000)


# ── AI Reply Suggestion ──

class LineAIReplyResponse(BaseModel):
    suggested_reply: str
    lead_context: Optional[dict] = None
