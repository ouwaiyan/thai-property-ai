"""AI endpoints — parse, tag, message, clean."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_data_entry
from app.config import settings
from app.dependencies import get_db
from app.models.user import User
from app.schemas.ai import (
    CleanDataRequest,
    CleanDataResponse,
    GenerateMessageRequest,
    GenerateMessageResponse,
    GenerateTagsRequest,
    GenerateTagsResponse,
    ParseLeadRequest,
    ParseLeadResponse,
)
from app.services.ai_service import (
    ai_clean_column_data,
    ai_generate_property_tags,
    ai_generate_sales_message,
    ai_parse_lead_needs,
)

router = APIRouter(prefix="/ai", tags=["AI"])


def _require_api_key():
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="ai.service_unavailable",
        )


@router.post("/parse-lead", response_model=ParseLeadResponse)
async def parse_lead(
    body: ParseLeadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_data_entry),
):
    """Parse natural-language client message into structured needs."""
    _require_api_key()
    try:
        return await ai_parse_lead_needs(db, body.message, body.language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ai.parse_failed||error={str(e)}")


@router.post("/generate-tags", response_model=GenerateTagsResponse)
async def generate_tags(
    body: GenerateTagsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_data_entry),
):
    """Generate marketing tags and highlights from property facts."""
    _require_api_key()
    try:
        return await ai_generate_property_tags(db, body.property_id, body.language)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ai.tag_generation_failed||error={str(e)}")


@router.post("/generate-message", response_model=GenerateMessageResponse)
async def generate_message(
    body: GenerateMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_data_entry),
):
    """Generate personalized sales copy for properties."""
    _require_api_key()
    from app.models.lead import Lead
    from sqlalchemy import select

    lead_result = await db.execute(select(Lead).where(Lead.id == body.lead_id))
    lead = lead_result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="lead.not_found")

    try:
        msg_map = await ai_generate_sales_message(
            db, lead, body.property_ids, body.language, body.tone
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ai.message_generation_failed||error={str(e)}")

    return GenerateMessageResponse(
        messages=[{"property_id": str(pid), "message": msg} for pid, msg in msg_map.items()]
    )


@router.post("/clean-data", response_model=CleanDataResponse)
async def clean_data(
    body: CleanDataRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_data_entry),
):
    """AI-assisted data cleaning suggestions for import."""
    _require_api_key()
    try:
        return await ai_clean_column_data(body.column_name, body.sample_values, body.expected_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ai.data_cleaning_failed||error={str(e)}")
