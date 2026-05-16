from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import TimestampMixin, gen_uuid


class Lead(Base, TimestampMixin):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    language = Column(String(10), nullable=False, default="zh")
    original_message = Column(Text, nullable=False)
    parsed_needs = Column(JSONB, nullable=True)
    target_location = Column(String(500), nullable=True)
    budget_min = Column(Integer, nullable=True)
    budget_max = Column(Integer, nullable=True)
    bedroom_count = Column(Integer, nullable=True)
    pet_required = Column(Boolean, default=False)
    preferred_transport = Column(String(50), nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    status = Column(String(20), nullable=False, default="new", index=True)
    source = Column(String(20), nullable=False, default="web")
    line_user_id = Column(String(64), nullable=True, index=True)
    assigned_agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    assigned_agent = relationship("User", foreign_keys=[assigned_agent_id], lazy="selectin")
    recommendations = relationship("Recommendation", back_populates="lead", cascade="all, delete-orphan")
    line_messages = relationship("LineMessage", backref="lead", lazy="selectin")
