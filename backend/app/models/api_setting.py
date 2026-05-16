from sqlalchemy import Boolean, Column, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base
from app.models.base import TimestampMixin, gen_uuid


class ApiSetting(Base, TimestampMixin):
    __tablename__ = "api_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    provider = Column(String(50), nullable=False, default="openai")
    key_name = Column(String(200), nullable=False, unique=True)
    encrypted_value = Column(Text, nullable=True)
    config_json = Column(JSONB, nullable=True)
    is_active = Column(Boolean, default=True)
