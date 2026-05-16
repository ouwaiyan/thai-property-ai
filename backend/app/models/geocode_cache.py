from sqlalchemy import Column, Float, String, DateTime
from sqlalchemy.sql import func

from app.database import Base


class GeocodeCache(Base):
    """Cached geocoding results to minimize API calls and costs."""

    __tablename__ = "geocode_cache"

    id = Column(String(36), primary_key=True, default=lambda: __import__("uuid").uuid4().hex)
    query_text = Column(String(500), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    display_name = Column(String(500), nullable=True)
    provider = Column(String(20), nullable=False, default="nominatim")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
