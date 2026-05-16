from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.models.base import TimestampMixin, gen_uuid


class LineMessage(Base, TimestampMixin):
    __tablename__ = "line_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    line_user_id = Column(String(64), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True)
    message_text = Column(Text, nullable=False)
    direction = Column(String(16), nullable=False, default="incoming")
    message_type = Column(String(16), nullable=False, default="text")
    reply_token = Column(String(255), nullable=True)
    source_type = Column(String(16), nullable=False, default="user")
    reply_status = Column(String(16), nullable=True)
