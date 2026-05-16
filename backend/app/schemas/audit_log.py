from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: UUID
    user_id: UUID
    action: str
    entity_type: str
    entity_id: Optional[UUID] = None
    before_json: Optional[dict] = None
    after_json: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
