from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, String, Text, event
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography

from app.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, gen_uuid


class Property(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "properties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    property_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False)
    building_name = Column(String(500), nullable=True)
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_geo = Column(Geography("POINT", srid=4326), nullable=True)
    district = Column(String(255), nullable=True)
    area = Column(String(255), nullable=True)
    nearest_bts = Column(String(255), nullable=True)
    nearest_mrt = Column(String(255), nullable=True)
    bedroom_count = Column(Integer, nullable=True)
    bathroom_count = Column(Integer, nullable=True)
    size_sqm = Column(Float, nullable=True)
    monthly_rent = Column(Integer, nullable=True)
    deposit_months = Column(Integer, nullable=True)
    status = Column(String(50), nullable=False, default="available", index=True)
    available_date = Column(Date, nullable=True)
    pet_allowed = Column(Boolean, default=False)
    contact_person = Column(String(255), nullable=True)
    contact_line = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    internal_note = Column(Text, nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_agent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by], lazy="selectin")
    assigned_agent = relationship("User", foreign_keys=[assigned_agent_id], lazy="selectin")
    images = relationship("PropertyImage", back_populates="property", cascade="all, delete-orphan")


@event.listens_for(Property, 'before_insert')
@event.listens_for(Property, 'before_update')
def _sync_location_geo(mapper, connection, target):
    """Auto-populate location_geo from latitude/longitude before flush."""
    if target.latitude is not None and target.longitude is not None:
        target.location_geo = f"SRID=4326;POINT({target.longitude} {target.latitude})"
    else:
        target.location_geo = None
