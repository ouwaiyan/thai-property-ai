from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import TimestampMixin, gen_uuid


class PropertyImage(Base, TimestampMixin):
    __tablename__ = "property_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False, index=True)
    image_url = Column(String(1000), nullable=False)
    sort_order = Column(Integer, default=0)
    is_cover = Column(Boolean, default=False)

    property = relationship("Property", back_populates="images")
