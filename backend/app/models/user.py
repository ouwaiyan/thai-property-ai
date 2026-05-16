from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import TimestampMixin, gen_uuid
from app.utils.enums import UserRole, UserStatus


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default=UserRole.VIEWER.value)
    status = Column(String(50), nullable=False, default=UserStatus.ACTIVE.value)

    created_properties = relationship(
        "Property", back_populates="creator", foreign_keys="Property.created_by"
    )
    assigned_properties = relationship(
        "Property", back_populates="assigned_agent", foreign_keys="Property.assigned_agent_id"
    )
