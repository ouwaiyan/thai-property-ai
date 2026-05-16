from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import TimestampMixin, gen_uuid


class ImportError(Base, TimestampMixin):
    __tablename__ = "import_errors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    import_job_id = Column(UUID(as_uuid=True), ForeignKey("import_jobs.id"), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    raw_data = Column(JSONB, nullable=True)
    error_messages = Column(JSONB, nullable=False)
    field_name = Column(String(100), nullable=True)

    import_job = relationship("ImportJob", back_populates="errors")
