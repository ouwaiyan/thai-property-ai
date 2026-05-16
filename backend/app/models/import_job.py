from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import TimestampMixin, gen_uuid


class ImportJob(Base, TimestampMixin):
    __tablename__ = "import_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    original_filename = Column(String(500), nullable=False)
    status = Column(String(20), nullable=False, default="uploaded", index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    total_rows = Column(Integer, default=0)
    success_rows = Column(Integer, default=0)
    error_rows = Column(Integer, default=0)
    column_mapping = Column(JSONB, nullable=True)
    file_path = Column(String(1000), nullable=False)

    creator = relationship("User", lazy="selectin")
    errors = relationship("ImportError", back_populates="import_job", cascade="all, delete-orphan")
