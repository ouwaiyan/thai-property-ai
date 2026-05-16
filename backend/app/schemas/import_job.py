from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ImportJobOut(BaseModel):
    id: UUID
    original_filename: str
    status: str
    created_by: UUID
    total_rows: int
    success_rows: int
    error_rows: int
    column_mapping: Optional[dict] = None
    file_path: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ImportErrorOut(BaseModel):
    id: UUID
    import_job_id: UUID
    row_number: int
    raw_data: Optional[dict] = None
    error_messages: list[str]
    field_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ImportJobDetail(ImportJobOut):
    errors: list[ImportErrorOut] = []


class FieldMappingRequest(BaseModel):
    mapping: dict[str, str]


class ImportConfirmRequest(BaseModel):
    overwrite_existing: bool = False


class ColumnInfo(BaseModel):
    header: str
    auto_detected_field: Optional[str] = None


class ColumnsResponse(BaseModel):
    columns: list[ColumnInfo]
    sheet_names: list[str] = []
    total_rows: int = 0


class PreviewRow(BaseModel):
    row_number: int
    data: dict[str, Optional[str]]
    errors: list[str] = []


class PreviewResponse(BaseModel):
    columns: list[ColumnInfo]
    rows: list[PreviewRow]
    total_rows: int
    preview_count: int


class ImportResult(BaseModel):
    import_job_id: UUID
    total_rows: int
    success_rows: int
    error_rows: int
    status: str
