"""Admin API key & configuration management."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.dependencies import get_db
from app.models.user import User
from app.services import settings_service
from app.utils.i18n import translate, get_request_language
from fastapi import Request

router = APIRouter(prefix="/admin/settings", tags=["API Settings"])


# ── Schemas ──────────────────────────────────────────────────────────────

class ApiSettingOut(BaseModel):
    id: str
    provider: str
    key_name: str
    value: str | None = None
    has_value: bool = False
    config_json: dict | None = None
    is_active: bool = True
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class ApiSettingUpsert(BaseModel):
    provider: str = Field(..., min_length=1, max_length=50)
    key_name: str = Field(..., min_length=1, max_length=200)
    value: str | None = None
    config_json: dict | None = None
    is_active: bool = True


class ApiSettingToggle(BaseModel):
    is_active: bool


class ApiSettingDeleteResponse(BaseModel):
    status: str


# ── Endpoints ────────────────────────────────────────────────────────────


@router.get("/", response_model=dict[str, list[ApiSettingOut]])
async def list_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all API settings grouped by provider."""
    return await settings_service.list_all_settings(db)


@router.put("/", response_model=ApiSettingOut)
async def upsert_setting(
    body: ApiSettingUpsert,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create or update an API setting."""
    try:
        result = await settings_service.upsert_setting(
            db,
            provider=body.provider,
            key_name=body.key_name,
            value=body.value,
            config_json=body.config_json,
            is_active=body.is_active,
        )
        return result
    except Exception:
        raise HTTPException(status_code=500, detail="settings.upsert_failed")


@router.patch("/{setting_id}", response_model=ApiSettingOut)
async def toggle_setting(
    setting_id: str,
    body: ApiSettingToggle,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Toggle an API setting's active state."""
    result = await settings_service.toggle_setting(db, setting_id, body.is_active)
    if not result:
        raise HTTPException(status_code=404, detail="settings.not_found")
    return result


@router.delete("/{setting_id}", response_model=ApiSettingDeleteResponse)
async def delete_setting(
    setting_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete an API setting."""
    deleted = await settings_service.delete_setting(db, setting_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="settings.not_found")
    return {"status": "deleted"}


class TestConnectionResponse(BaseModel):
    success: bool
    message: str


@router.post("/test-connection/{provider}", response_model=TestConnectionResponse)
async def test_connection(
    provider: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Test API connection for a provider without leaking keys."""
    return await settings_service.test_connection(db, provider)
