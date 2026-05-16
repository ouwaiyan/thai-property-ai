from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import TimestampMixin, gen_uuid


class Recommendation(Base, TimestampMixin):
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    distance_meters = Column(Integer, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    route_mode = Column(String(20), nullable=True)
    match_score = Column(Float, nullable=False, default=0.0)
    reason_json = Column(JSONB, nullable=True)
    ai_message = Column(Text, nullable=True)
    sent_to_customer = Column(Boolean, default=False)

    lead = relationship("Lead", back_populates="recommendations")
    property = relationship("Property", lazy="selectin")
