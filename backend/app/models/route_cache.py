from sqlalchemy import Column, Float, Integer, String

from app.database import Base
from app.models.base import TimestampMixin


class RouteCache(Base, TimestampMixin):
    """Cached route matrix results to minimize Google Routes API costs."""

    __tablename__ = "route_cache"

    cache_key = Column(String(64), primary_key=True)  # SHA256 hex digest
    origin_lat = Column(Float, nullable=False)
    origin_lng = Column(Float, nullable=False)
    dest_lat = Column(Float, nullable=False)
    dest_lng = Column(Float, nullable=False)
    travel_mode = Column(String(10), nullable=False)
    distance_meters = Column(Integer, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
