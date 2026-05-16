from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_data_entry
from app.dependencies import get_db
from app.models.user import User
from app.schemas import PaginatedResponse
from app.schemas.import_job import (
    ColumnsResponse,
    FieldMappingRequest,
    ImportConfirmRequest,
    ImportErrorOut,
    ImportJobDetail,
    ImportJobOut,
    ImportResult,
    PreviewResponse,
)
from app.services import import_service

router = APIRouter(prefix="/imports", tags=["Imports"])


@router.post("/upload", response_model=ImportJobOut, status_code=201)
async def upload_import_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_data_entry),
):
    job = await import_service.upload_file(db, file, current_user)
    return ImportJobOut.model_validate(job)


@router.get("/{job_id}/columns", response_model=ColumnsResponse)
async def get_columns(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await import_service.get_columns(db, job_id)


@router.put("/{job_id}/preview", response_model=PreviewResponse)
async def preview_import(
    job_id: UUID,
    body: FieldMappingRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mapping = body.mapping if body else None
    return await import_service.preview(db, job_id, mapping)


@router.put("/{job_id}/map", response_model=ImportJobOut)
async def map_fields(
    job_id: UUID,
    body: FieldMappingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_data_entry),
):
    job = await import_service.map_fields(db, job_id, body.mapping)
    return ImportJobOut.model_validate(job)


@router.post("/{job_id}/confirm", response_model=ImportResult)
async def confirm_import(
    job_id: UUID,
    body: ImportConfirmRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_data_entry),
):
    overwrite = body.overwrite_existing if body else False
    return await import_service.confirm_import(db, job_id, current_user, overwrite)


@router.get("/", response_model=PaginatedResponse)
async def list_import_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = await import_service.get_import_jobs(db, page=page, page_size=page_size)
    return PaginatedResponse(
        items=[ImportJobOut.model_validate(j) for j in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/{job_id}", response_model=ImportJobDetail)
async def get_import_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await import_service.get_import_job(db, job_id)
    errors = await import_service.get_import_errors(db, job_id)
    return ImportJobDetail(
        **ImportJobOut.model_validate(job).model_dump(),
        errors=[ImportErrorOut.model_validate(e) for e in errors],
    )


@router.get("/{job_id}/errors", response_model=list[ImportErrorOut])
async def get_import_errors(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    errors = await import_service.get_import_errors(db, job_id)
    return [ImportErrorOut.model_validate(e) for e in errors]
